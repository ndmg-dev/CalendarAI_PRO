"""Chat blueprint — AI chat interface."""

from flask import Blueprint

chat_bp = Blueprint(
    "chat",
    __name__,
    template_folder="templates",
    url_prefix="/chat",
)

from app.blueprints.chat import routes  # noqa: E402, F401
