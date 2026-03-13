"""Event model — scheduling events for users."""

import uuid

from sqlalchemy import String, Text, DateTime, ForeignKey, Index, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Event(db.Model):
    """A scheduling event belonging to a user."""

    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_user_start", "user_id", "start_datetime"),
        Index("ix_events_user_status", "user_id", "status"),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_datetime: Mapped[str] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_datetime: Mapped[str] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    timezone: Mapped[str] = mapped_column(
        String(64), nullable=False, default="America/Sao_Paulo",
        comment="Original timezone of the event"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active",
        comment="active | cancelled"
    )

    notification_sent: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="Whether a reminder email has been sent for this event"
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
    user: Mapped["User"] = relationship("User", back_populates="events")  # noqa: F821
    calendar_sync: Mapped["CalendarSync | None"] = relationship(  # noqa: F821
        "CalendarSync", back_populates="event", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Event {self.title!r} ({self.status})>"

    def to_dict(self) -> dict:
        """Serialize event for JSON / FullCalendar."""
        result = {
            "id": self.id,
            "title": self.title,
            "start": self.start_datetime.isoformat() if self.start_datetime else None,
            "end": self.end_datetime.isoformat() if self.end_datetime else None,
            "extendedProps": {
                "description": self.description,
                "status": self.status,
                "timezone": self.timezone,
            },
        }
        if self.calendar_sync:
            result["extendedProps"]["syncStatus"] = self.calendar_sync.sync_status
        return result
