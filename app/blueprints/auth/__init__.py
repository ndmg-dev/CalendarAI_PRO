"""Auth blueprint — Google OAuth login/logout/callback."""

from flask import Blueprint

auth_bp = Blueprint(
    "auth",
    __name__,
    template_folder="templates",
    url_prefix="/auth",
)

from app.blueprints.auth import routes  # noqa: E402, F401
