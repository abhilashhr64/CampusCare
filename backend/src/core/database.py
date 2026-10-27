import uuid
from typing import Generator
from datetime import datetime
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker, Session, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from src.core.config import settings

# Naming convention for foreign keys, constraints, and indexes
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    metadata = metadata


class TenantBase(Base):
    """Abstract base model for all tenant-scoped tables (Rule TN-1).
    Every tenant-owned table must include non-null college_id.
    """
    __abstract__ = True

    college_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        doc="Tenant college isolation identifier (Rule TN-1)",
    )


# Engine for running migrations (runs as privileged migrator role)
migrator_engine = create_engine(
    settings.DB_MIGRATOR_URL,
    echo=settings.DEBUG and settings.ENVIRONMENT == "development",
    pool_pre_ping=True,
)

# Engine for application runtime (runs as campuscare_app with NOBYPASSRLS)
app_engine = create_engine(
    settings.DB_APP_URL,
    echo=settings.DEBUG and settings.ENVIRONMENT == "development",
    pool_pre_ping=True,
)

SessionMigrator = sessionmaker(autocommit=False, autoflush=False, bind=migrator_engine)
SessionApp = sessionmaker(autocommit=False, autoflush=False, bind=app_engine)


def get_app_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields an application session connecting as non-owner role."""
    session = SessionApp()
    try:
        yield session
    finally:
        session.close()


def get_migrator_db() -> Generator[Session, None, None]:
    """Yields a migration/admin session connecting as privileged migrator role."""
    session = SessionMigrator()
    try:
        yield session
    finally:
        session.close()
