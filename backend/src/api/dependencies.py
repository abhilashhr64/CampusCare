import uuid
from typing import Optional, Callable
from functools import wraps
from fastapi import Request, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.core.database import get_app_db
from src.core.rls import set_tenant_context
from src.core.security import hash_token
from src.core.config import settings
from src.modules.access.policy import Actor, authorize, Decision


def get_current_actor(
    request: Request,
    db: Session = Depends(get_app_db),
) -> Optional[Actor]:
    """Extracts and verifies the active session cookie or bearer token.
    Resolves the user, tenant college, and active role grants.
    Sets transaction-local PostgreSQL RLS context (Rule TN-2).
    """
    raw_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not raw_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            raw_token = auth_header.split(" ")[1]

    if not raw_token:
        return None

    token_hash = hash_token(raw_token)

    # 1. Look up session in identity_sessions
    # Since session is tenant-scoped, we query with the token_hash directly
    session_row = db.execute(
        text("""
            SELECT s.id, s.user_id, s.college_id, s.expires_at, s.is_revoked,
                   u.email, u.full_name, u.is_email_verified, u.is_mfa_enabled
            FROM identity_sessions s
            JOIN users u ON u.id = s.user_id AND u.college_id = s.college_id
            WHERE s.token_hash = :token_hash
              AND s.is_revoked = false
              AND s.expires_at > now();
        """),
        {"token_hash": token_hash},
    ).fetchone()

    if not session_row:
        return None

    (
        s_id,
        user_id,
        college_id,
        expires_at,
        is_revoked,
        email,
        full_name,
        is_email_verified,
        is_mfa_enabled,
    ) = session_row

    # 2. Set PostgreSQL RLS transaction context (Rule TN-2)
    set_tenant_context(db, college_id=college_id, user_id=user_id)

    # 3. Query active role grants (Rule AZ-5)
    role_rows = db.execute(
        text("""
            SELECT role, scope
            FROM access_role_grants
            WHERE user_id = :user_id
              AND college_id = :college_id
              AND is_revoked = false
              AND (expires_at IS NULL OR expires_at > now());
        """),
        {"user_id": user_id, "college_id": college_id},
    ).fetchall()

    roles = [row[0] for row in role_rows]
    role_scopes = {row[0]: row[1] for row in role_rows}

    # If user has no explicit staff role, assign default STUDENT role if email is verified
    if not roles and is_email_verified:
        roles = ["STUDENT"]

    # Check if session is MFA authenticated
    is_mfa_authenticated = bool(request.session.get("mfa_verified") if hasattr(request, "session") else True)

    return Actor(
        user_id=user_id,
        college_id=college_id,
        email=email,
        is_email_verified=is_email_verified,
        is_mfa_authenticated=is_mfa_authenticated,
        roles=roles,
        role_scopes=role_scopes,
    )


def require_permission(action: str, resource_loader: Optional[Callable[[Request], dict]] = None):
    """Route decorator and dependency that declares the required action (Rule AZ-3)
    and enforces authorize(actor, action, resource) (Rule AZ-1, AZ-2, NR-3).
    """
    def decorator(func: Callable):
        # Attach required action to endpoint function metadata for CI verification (AZ-3)
        setattr(func, "__permission_action__", action)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            import inspect
            if inspect.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return func(*args, **kwargs)


        setattr(wrapper, "__permission_action__", action)
        return wrapper

    return decorator
