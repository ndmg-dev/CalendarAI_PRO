"""Alembic environment configuration — integrated with Flask app factory."""

from logging.config import fileConfig

from alembic import context
from flask import current_app

from app import create_app
from app.extensions import db

# Import all models so Alembic can detect them
import app.models  # noqa: F401

# Alembic Config object
config = context.config

# Set up logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Create Flask app for context
flask_app = create_app()

# Use the app's database URI
with flask_app.app_context():
    config.set_main_option("sqlalchemy.url", flask_app.config["SQLALCHEMY_DATABASE_URI"])

target_metadata = db.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
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
    """Run migrations in 'online' mode."""
    with flask_app.app_context():
        connectable = db.engine

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
