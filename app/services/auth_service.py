"""Authentication service — Google OAuth, token encryption, user management."""

import logging

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app

from app.extensions import db
from app.models.user import User

logger = logging.getLogger(__name__)


class AuthService:
    """Handles user creation/lookup and token encryption for Google OAuth."""

    @staticmethod
    def get_or_create_user(google_userinfo: dict) -> User:
        """Find an existing user by google_id or create a new one.

        Args:
            google_userinfo: Dict with keys from Google's userinfo endpoint:
                sub, email, name, picture, hd (optional).
        """
        google_id = google_userinfo["sub"]
        user = db.session.query(User).filter_by(google_id=google_id).first()

        if user:
            # Update mutable profile fields on each login
            user.display_name = google_userinfo.get("name", user.display_name)
            user.avatar_url = google_userinfo.get("picture", user.avatar_url)
            user.email = google_userinfo.get("email", user.email)
            user.domain = google_userinfo.get("hd", user.domain)
            db.session.commit()
            logger.info("User logged in: %s", user.email)
        else:
            user = User(
                google_id=google_id,
                email=google_userinfo["email"],
                display_name=google_userinfo.get("name"),
                avatar_url=google_userinfo.get("picture"),
                domain=google_userinfo.get("hd"),
            )
            db.session.add(user)
            db.session.commit()
            logger.info("New user created: %s", user.email)

        return user

    @staticmethod
    def encrypt_token(token: str) -> str:
        """Encrypt a token (e.g. refresh_token) using Fernet symmetric encryption."""
        key = current_app.config.get("ENCRYPTION_KEY")
        if not key:
            raise RuntimeError("ENCRYPTION_KEY is not configured")
        f = Fernet(key.encode() if isinstance(key, str) else key)
        return f.encrypt(token.encode()).decode()

    @staticmethod
    def decrypt_token(encrypted_token: str) -> str:
        """Decrypt a previously encrypted token."""
        key = current_app.config.get("ENCRYPTION_KEY")
        if not key:
            raise RuntimeError("ENCRYPTION_KEY is not configured")
        f = Fernet(key.encode() if isinstance(key, str) else key)
        try:
            return f.decrypt(encrypted_token.encode()).decode()
        except InvalidToken:
            logger.error("Failed to decrypt token — key may have rotated")
            raise

    @staticmethod
    def store_refresh_token(user: User, refresh_token: str) -> None:
        """Encrypt and store Google refresh token for Calendar sync."""
        user.google_refresh_token = AuthService.encrypt_token(refresh_token)
        user.calendar_sync_enabled = True
        db.session.commit()
        logger.info("Stored refresh token for user %s", user.email)

    @staticmethod
    def get_refresh_token(user: User) -> str | None:
        """Retrieve and decrypt the stored refresh token."""
        if not user.google_refresh_token:
            return None
        try:
            return AuthService.decrypt_token(user.google_refresh_token)
        except Exception:
            return None
