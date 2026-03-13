"""CalendAI PRO — Flask application factory."""

import os
import logging

from flask import Flask, redirect, url_for
from flask_login import current_user

from app.config import config_map
from app.extensions import db, login_manager


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config_name: One of 'development', 'production', 'testing'.
                     Defaults to FLASK_ENV environment variable.
    """
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config.from_object(config_map[config_name])

    # ── Logging ──────────────────────────────────────────
    logging.basicConfig(
        level=logging.DEBUG if app.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app.logger.info("CalendAI PRO starting in '%s' mode", config_name)

    # ── Extensions ───────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)

    # ── User loader for Flask-Login ──────────────────────
    @login_manager.user_loader
    def load_user(user_id: str):
        from app.models.user import User
        return db.session.get(User, user_id)

    # ── Blueprints ───────────────────────────────────────
    from app.blueprints.auth import auth_bp
    from app.blueprints.chat import chat_bp
    from app.blueprints.agenda import agenda_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(agenda_bp)

    # ── Root redirect ────────────────────────────────────
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("chat.index"))
        return redirect(url_for("auth.login"))

    # ── Health check ─────────────────────────────────────
    @app.route("/health")
    def health():
        return {"status": "ok", "app": "CalendAI PRO"}, 200

    # ── Context processors ───────────────────────────────
    @app.context_processor
    def inject_app_name():
        return {"app_name": "CalendAI PRO"}

    # ── Background Tasks ─────────────────────────────────
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        from app.scheduler import init_scheduler
        init_scheduler(app)

    return app
