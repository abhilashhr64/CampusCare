import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add backend directory to sys.path so src.* is importable
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from src.core.config import settings
from src.core.database import Base

# Import all models to register them on Base.metadata
import src.modules.tenancy.models
import src.modules.identity.models
import src.modules.access.models
import src.modules.directory.models
import src.modules.audit.models
import src.modules.attendance.models
import src.modules.complaints.models
import src.modules.feedback.models
import src.modules.knowledge.models
import src.modules.assistant.models
import src.modules.notifications.models
import src.modules.analytics.models
import src.core.outbox


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the migrator DB URL dynamically from settings (Rule NR-2, TN-3)
config.set_main_option("sqlalchemy.url", settings.DB_MIGRATOR_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
