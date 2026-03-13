"""User repository — data access layer for users."""

from app.extensions import db
from app.models.user import User


class UserRepository:
    """Data access for User model."""

    @staticmethod
    def get_by_id(user_id: str) -> User | None:
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_google_id(google_id: str) -> User | None:
        return db.session.query(User).filter_by(google_id=google_id).first()

    @staticmethod
    def get_by_email(email: str) -> User | None:
        return db.session.query(User).filter_by(email=email).first()
