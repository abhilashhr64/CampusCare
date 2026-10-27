from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.orm import Session
from src.core.database import get_app_db
from src.core.config import settings
from src.api.dependencies import require_permission, get_current_actor
from src.modules.access.policy import Actor, authorize
from src.modules.identity.service import (
    IdentityService,
    StudentSignupRequest,
    LoginRequest,
    VerifyCodeRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Identity & Authentication"])


@router.post("/signup-student", status_code=status.HTTP_201_CREATED)
@require_permission("auth:signup_student")
def signup_student(
    data: StudentSignupRequest,
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    decision = authorize(actor, "auth:signup_student")
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    try:
        user, code = IdentityService.register_student(db, data)
        return {
            "message": "Student registered successfully. Please verify your email.",
            "user_id": user.id,
            "synthetic_verification_code": code,  # Returned in dev/test per synthetic rules
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/verify-code")
@require_permission("auth:verify_code")
def verify_email_code(
    data: VerifyCodeRequest,
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    decision = authorize(actor, "auth:verify_code")
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    success = IdentityService.verify_email_code(db, data.college_id, data.email, data.code)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification code.")
    return {"message": "Email verified successfully. You may now log in."}


@router.post("/login", response_model=TokenResponse)
@require_permission("auth:login")
def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    decision = authorize(actor, "auth:login")
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    try:
        user, raw_token, expires_at = IdentityService.authenticate_user(
            db,
            college_id=data.college_id,
            email=data.email,
            password=data.password,
            ip_address=client_ip,
            user_agent=user_agent,
        )

        # Set secure httpOnly cookie (Rule C5, ADR-003)
        response.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=raw_token,
            httponly=settings.SESSION_COOKIE_HTTPONLY,
            secure=settings.SESSION_COOKIE_SECURE,
            samesite=settings.SESSION_COOKIE_SAMESITE,
            max_age=settings.SESSION_LIFETIME_SECONDS,
        )

        user_resp = UserResponse(
            id=user.id,
            college_id=user.college_id,
            email=user.email,
            full_name=user.full_name,
            is_email_verified=user.is_email_verified,
            is_mfa_enabled=user.is_mfa_enabled,
            roles=["STUDENT"] if user.is_email_verified else [],
            role_scopes={},
        )

        return TokenResponse(
            session_token=raw_token,
            expires_at=expires_at,
            user=user_resp,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout")
@require_permission("user:get_profile")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_app_db),
    actor: Actor = Depends(get_current_actor),
):
    decision = authorize(actor, "user:get_profile")
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    raw_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not raw_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            raw_token = auth_header.split(" ")[1]

    if raw_token:
        IdentityService.revoke_session(db, raw_token)

    response.delete_cookie(settings.SESSION_COOKIE_NAME)
    return {"message": "Logged out successfully."}


@router.get("/me", response_model=UserResponse)
@require_permission("user:get_profile")
def get_current_user_profile(
    actor: Actor = Depends(get_current_actor),
):
    decision = authorize(actor, "user:get_profile", resource={"user_id": actor.user_id if actor else None})
    if not decision.allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=decision.reason_code)

    return UserResponse(
        id=actor.user_id,
        college_id=actor.college_id,
        email=actor.email,
        full_name="Current User",
        is_email_verified=actor.is_email_verified,
        is_mfa_enabled=actor.is_mfa_authenticated,
        roles=actor.roles,
        role_scopes=actor.role_scopes,
    )
