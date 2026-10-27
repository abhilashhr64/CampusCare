import uuid
from typing import Optional
from sqlalchemy import text, event
from sqlalchemy.orm import Session


@event.listens_for(Session, "after_begin")
def _receive_after_begin(session: Session, transaction, connection) -> None:
    """Ensures PostgreSQL transaction-local RLS variables are applied to all new transactions."""
    college_id = session.info.get("college_id")
    if college_id:
        connection.execute(
            text("SELECT set_config('app.current_college_id', :college_id, true)"),
            {"college_id": college_id},
        )
        user_id = session.info.get("user_id")
        if user_id:
            connection.execute(
                text("SELECT set_config('app.current_user_id', :user_id, true)"),
                {"user_id": user_id},
            )
        else:
            connection.execute(text("SELECT set_config('app.current_user_id', '', true)"))


def set_tenant_context(session: Session, college_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> None:
    """Sets transaction-local tenant and actor context for PostgreSQL RLS (Rule TN-2).
    
    The third argument 'true' ensures the configuration parameter is transaction-local
    (equivalent to SET LOCAL) and automatically resets on transaction commit or rollback.
    The session.info dict preserves context across transaction boundaries within the session.
    """
    session.info["college_id"] = str(college_id)
    session.info["user_id"] = str(user_id) if user_id else ""

    session.execute(
        text("SELECT set_config('app.current_college_id', :college_id, true)"),
        {"college_id": str(college_id)},
    )
    if user_id:
        session.execute(
            text("SELECT set_config('app.current_user_id', :user_id, true)"),
            {"user_id": str(user_id)},
        )
    else:
        session.execute(
            text("SELECT set_config('app.current_user_id', '', true)")
        )


def clear_tenant_context(session: Session) -> None:
    """Resets the tenant context to empty, causing all RLS queries to fail closed."""
    session.info.pop("college_id", None)
    session.info.pop("user_id", None)
    session.execute(text("SELECT set_config('app.current_college_id', '', true)"))
    session.execute(text("SELECT set_config('app.current_user_id', '', true)"))

