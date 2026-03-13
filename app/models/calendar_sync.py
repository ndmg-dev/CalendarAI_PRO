"""CalendarSync model — Google Calendar sync metadata per event."""

import uuid

from sqlalchemy import String, Text, DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class CalendarSync(db.Model):
    """Tracks synchronization state between a local event and Google Calendar."""

    __tablename__ = "calendar_syncs"
    __table_args__ = (
        Index("ix_calendar_syncs_user_status", "user_id", "sync_status"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    event_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("events.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    google_calendar_id: Mapped[str] = mapped_column(
        String(255), nullable=False, default="primary",
        comment="Google Calendar ID (default: primary)"
    )
    google_event_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
        comment="Event ID in Google Calendar"
    )
    sync_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
        comment="synced | pending | error"
    )
    last_synced_at: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sync_error: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Last sync error message"
    )
    etag: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
        comment="Google Calendar event etag for conflict detection"
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
    event: Mapped["Event"] = relationship("Event", back_populates="calendar_sync")  # noqa: F821
    user: Mapped["User"] = relationship("User")  # noqa: F821

    def __repr__(self) -> str:
        return f"<CalendarSync event={self.event_id} status={self.sync_status}>"
