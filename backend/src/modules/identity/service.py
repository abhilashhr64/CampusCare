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
