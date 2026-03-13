"""ChatMessage model — persistent storage for AI conversations."""

import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class ChatMessage(db.Model):
    """A single message in a chat history, stored in the DB."""

    __tablename__ = "chat_messages"

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
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="user | assistant"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Store when it was sent
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationship
    user: Mapped["User"] = relationship("User", backref="chat_messages")  # noqa: F821

    def __repr__(self) -> str:
        return f"<ChatMessage {self.role}: {self.content[:20]}...>"

    def to_dict(self) -> dict:
        """Serialize for session/API."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.created_at.isoformat() if self.created_at else None
        }
