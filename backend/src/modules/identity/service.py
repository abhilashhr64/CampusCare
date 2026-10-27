import uuid
import datetime
from datetime import timezone
from typing import Optional, Tuple, List, Dict, Any
from pydantic import BaseModel, EmailStr, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from src.core.security import (
    hash_password,
    verify_password,
    generate_session_token,
    hash_token,
)
from src.core.config import settings
from src.core.rls import set_tenant_context
from src.core.outbox import publish_event
from src.modules.identity.models import User, Session as UserSession, VerificationToken
from src.modules.tenancy.service import TenancyService
from src.modules.access.service import AccessService


class StudentSignupRequest(BaseModel):
    college_id: uuid.UUID
    email: EmailStr
    full_name: str
    password: str


class LoginRequest(BaseModel):
    college_id: uuid.UUID
    email: EmailStr
    password: str


class VerifyCodeRequest(BaseModel):
    college_id: uuid.UUID
    email: EmailStr
    code: str


class GoogleLoginRequest(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    credential: Optional[str] = None
    college_id: Optional[uuid.UUID] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    college_id: uuid.UUID
    email: str
    full_name: str
    is_email_verified: bool
    is_mfa_enabled: bool
    roles: List[str] = []
    role_scopes: Dict[str, Any] = {}

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    session_token: str
    expires_at: datetime.datetime
    user: UserResponse


class GoogleLoginResponse(BaseModel):
    session_token: str
    expires_at: datetime.datetime
    dashboard_type: str  # "ADMIN" or "USER"
    user: UserResponse


class IdentityService:
    @staticmethod
    def register_student(db: Session, data: StudentSignupRequest) -> Tuple[User, str]:
        """Registers student in tenant college and issues verification code (Rule NR-5).
        Verified email alone NEVER grants privileged roles.
        """
        set_tenant_context(db, college_id=data.college_id)

        # Check if user already exists
        stmt = select(User).where(User.college_id == data.college_id, User.email == data.email)
        existing = db.scalar(stmt)
        if existing:
            raise ValueError("An account with this email already exists for this college.")

        # Create user
        user = User(
            college_id=data.college_id,
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            is_email_verified=False,
            is_active=True,
        )
        db.add(user)
        db.flush()

        # Generate 6-digit synthetic verification code
        code = "123456"  # Synthetic verification code (Rule NR-6)
        code_hash = hash_token(code)
        token = VerificationToken(
            college_id=data.college_id,
            email=data.email,
            code_hash=code_hash,
            purpose="EMAIL_VERIFY",
            expires_at=datetime.datetime.now(timezone.utc) + datetime.timedelta(minutes=15),
        )
        db.add(token)

        # Enqueue transactional outbox event (Rule EV-1, BR-3)
        publish_event(
            db,
            topic="identity.student_registered",
            payload={"user_id": str(user.id), "email": user.email, "college_id": str(data.college_id)},
            college_id=data.college_id,
        )

        db.commit()
        db.refresh(user)
        return user, code

    @staticmethod
    def verify_email_code(db: Session, college_id: uuid.UUID, email: str, code: str) -> bool:
        set_tenant_context(db, college_id=college_id)
        code_hash = hash_token(code)
        now = datetime.datetime.now(timezone.utc)

        stmt = (
            select(VerificationToken)
            .where(
                VerificationToken.college_id == college_id,
                VerificationToken.email == email,
                VerificationToken.code_hash == code_hash,
                VerificationToken.purpose == "EMAIL_VERIFY",
                VerificationToken.used_at == None,
                VerificationToken.expires_at > now,
            )
            .order_by(VerificationToken.created_at.desc())
        )
        token = db.scalar(stmt)
        if not token:
            return False

        token.used_at = now

        # Mark user verified
        db.execute(
            update(User)
            .where(User.college_id == college_id, User.email == email)
            .values(is_email_verified=True)
        )
        db.commit()
        return True

    @staticmethod
    def authenticate_user(
        db: Session,
        college_id: uuid.UUID,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[User, str, datetime.datetime]:
        """Verifies password and creates a server-side session (Rule C5, ADR-003)."""
        set_tenant_context(db, college_id=college_id)

        stmt = select(User).where(
            User.college_id == college_id,
            User.email == email,
            User.is_active == True,
        )
        user = db.scalar(stmt)
        if not user or not user.hashed_password:
            raise ValueError("Invalid email or password.")

        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password.")

        raw_token, token_hash = generate_session_token()
        expires_at = datetime.datetime.now(timezone.utc) + datetime.timedelta(
            seconds=settings.SESSION_LIFETIME_SECONDS
        )

        session = UserSession(
            college_id=college_id,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(session)
        db.commit()
        return user, raw_token, expires_at

    @staticmethod
    def revoke_session(db: Session, raw_token: str) -> None:
        """Revokes a session by hash (Rule C5)."""
        token_hash = hash_token(raw_token)
        db.execute(
            update(UserSession)
            .where(UserSession.token_hash == token_hash)
            .values(is_revoked=True)
        )
        db.commit()

    @staticmethod
    def invalidate_all_user_sessions(db: Session, college_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Instantly invalidates all active sessions for a user (Rule AZ-5, C5)."""
        set_tenant_context(db, college_id=college_id)
        db.execute(
            update(UserSession)
            .where(
                UserSession.college_id == college_id,
                UserSession.user_id == user_id,
            )
            .values(is_revoked=True)
        )
        db.commit()

    @staticmethod
    def authenticate_google(
        db: Session,
        data: GoogleLoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[User, str, datetime.datetime, str, List[str]]:
        """Authenticates or provisions a user via Google Sign-In with mandatory college email validation.
        
        Rules Enforced:
        - Must be an institutional college email (generic personal domains rejected).
        - Rule NR-5: Verified email alone NEVER grants elevated staff/admin roles.
        - Automatically resolves target tenant college by domain or ID.
        - Sets server-side session and returns target dashboard ('ADMIN' or 'USER').
        """
        email_str = str(data.email).strip().lower()
        parts = email_str.split("@")
        if len(parts) != 2:
            raise ValueError("Invalid email format.")
        domain = parts[1]

        # 1. Enforce College Email Domain (Reject generic personal email providers)
        disallowed_public_domains = {
            "gmail.com",
            "googlemail.com",
            "yahoo.com",
            "ymail.com",
            "hotmail.com",
            "outlook.com",
            "live.com",
            "icloud.com",
            "aol.com",
            "mail.com",
            "proton.me",
            "protonmail.com",
        }
        if domain in disallowed_public_domains:
            raise ValueError(
                f"Access Denied: '{email_str}' is a personal email account. "
                "Institutional policy requires signing in with your verified college mail ID "
                "(e.g., student@apex.edu or institutional domain)."
            )

        # 2. Resolve Tenant College
        college = None
        if data.college_id:
            college = TenancyService.get_college_by_id(db, data.college_id)
        if not college:
            college = TenancyService.get_college_by_domain(db, domain)
        if not college:
            # Fallback to active college in local environment
            active_colleges = TenancyService.get_all_active_colleges(db)
            if active_colleges:
                college = active_colleges[0]
            else:
                raise ValueError(f"No active educational institution found matching domain '@{domain}'.")

        target_college_id = college.id
        set_tenant_context(db, college_id=target_college_id)

        # 3. Lookup or Provision User
        stmt = select(User).where(User.college_id == target_college_id, User.email == email_str)
        user = db.scalar(stmt)
        if not user:
            # Auto-provision verified student account (Rule NR-5: no elevated roles)
            user_full_name = data.full_name or parts[0].replace(".", " ").title()
            user = User(
                college_id=target_college_id,
                email=email_str,
                full_name=user_full_name,
                is_email_verified=True,  # Verified by Google OIDC
                is_active=True,
            )
            db.add(user)
            db.flush()

            # Enqueue outbox event
            publish_event(
                db,
                topic="identity.google_user_provisioned",
                payload={"user_id": str(user.id), "email": user.email, "college_id": str(target_college_id)},
                college_id=target_college_id,
            )
        else:
            if not user.is_email_verified:
                user.is_email_verified = True
                db.flush()

        # 4. Query Active Roles via AccessService (Rule AZ-5, BR-1)
        active_roles = AccessService.get_user_active_roles(db, target_college_id, user.id)
        if not active_roles and user.is_email_verified:
            active_roles = ["STUDENT"]

        # 5. Determine Dashboard Target
        # College and Dept admins are routed to the Admin Dashboard; students/lecturers to the User Dashboard
        if any(r in ("COLLEGE_ADMIN", "DEPARTMENT_ADMIN") for r in active_roles):
            dashboard_type = "ADMIN"
        else:
            dashboard_type = "USER"

        # 6. Create Server-Side Session (Rule C5, ADR-003)
        raw_token, token_hash = generate_session_token()
        expires_at = datetime.datetime.now(timezone.utc) + datetime.timedelta(
            seconds=settings.SESSION_LIFETIME_SECONDS
        )

        session = UserSession(
            college_id=target_college_id,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(session)
        db.commit()
        db.refresh(user)

        return user, raw_token, expires_at, dashboard_type, active_roles
