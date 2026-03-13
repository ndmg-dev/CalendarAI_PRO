"""Agenda blueprint — calendar/schedule views."""

from flask import Blueprint

agenda_bp = Blueprint(
    "agenda",
    __name__,
    template_folder="templates",
    url_prefix="/agenda",
)

from app.blueprints.agenda import routes  # noqa: E402, F401
