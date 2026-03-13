"""User model — Google OAuth identity and preferences."""

import uuid

from flask_login import UserMixin
from sqlalchemy import String, Boolean, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class User(UserMixin, db.Model):
    """Application user, authenticated via Google OAuth."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    google_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    domain: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Google Workspace domain (hd claim)"
    )
    timezone: Mapped[str] = mapped_column(
        String(64), nullable=False, default="America/Sao_Paulo"
    )
    google_refresh_token: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Encrypted refresh token for Calendar sync"
    )
    calendar_sync_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    events: Mapped[list["Event"]] = relationship(  # noqa: F821
        "Event", back_populates="user", cascade="all, delete-orphan", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"

    def get_id(self) -> str:
        """Override for Flask-Login (expects string)."""
        return str(self.id)
