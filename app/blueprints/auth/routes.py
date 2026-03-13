"""Auth routes — Google OAuth login, callback, logout, and Calendar sync enable."""

import logging
from datetime import datetime

from authlib.integrations.flask_client import OAuth
from flask import redirect, url_for, session, flash, current_app, request, render_template
from flask_login import login_user, logout_user, login_required, current_user

from app.blueprints.auth import auth_bp
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

# OAuth instance (configured in register_oauth)
oauth = OAuth()


def register_oauth(app):
    """Register the Google OAuth provider with the Flask app."""
    oauth.init_app(app)
    oauth.register(
        name="google",
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        client_kwargs={
            "scope": " ".join(app.config["GOOGLE_CALENDAR_SCOPES"]),
            "leeway": 60,  # Tolerate up to 60s clock skew
        },
    )


@auth_bp.record_once
def on_register(state):
    """Called when the blueprint is registered — set up OAuth."""
    register_oauth(state.app)


@auth_bp.route("/login")
def login():
    """Render login page."""
    if current_user.is_authenticated and not request.args.get("logged_out"):
        return redirect(url_for("chat.index"))
    
    return render_template("auth/login.html")


@auth_bp.route("/privacy")
def privacy():
    """Render Privacy Policy page."""
    return render_template("auth/privacy.html")


@auth_bp.route("/google")
def google_login():
    """Redirect user to Google OAuth consent screen."""
    redirect_uri = url_for("auth.callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/callback")
def callback():
    """Handle Google OAuth callback — exchange code for tokens, create/update user."""
    import time
    logger.info("System time.time() = %s, local = %s", time.time(), datetime.now())

    try:
        token = oauth.google.authorize_access_token(leeway=86400)
    except Exception as e:
        logger.error("OAuth token exchange error: %s", str(e), exc_info=True)
        flash("Erro na autenticação. Tente novamente.", "error")
        return redirect(url_for("auth.login"))

    try:
        # Get user info from Google
        userinfo = token.get("userinfo")
        if not userinfo:
            # Fallback: fetch from userinfo endpoint
            resp = oauth.google.get("https://openidconnect.googleapis.com/v1/userinfo")
            userinfo = resp.json()

        if not userinfo or not userinfo.get("sub"):
            flash("Não foi possível obter dados do usuário.", "error")
            return redirect(url_for("auth.login"))

        logger.info("Google userinfo received: email=%s, sub=%s", userinfo.get("email"), userinfo.get("sub"))

        # Create or update user
        user = AuthService.get_or_create_user(userinfo)
        logger.info("User record ready: id=%s, email=%s", user.id, user.email)

        login_user(user, remember=True)
        logger.info("login_user() called, is_authenticated=%s", current_user.is_authenticated)

        # Store refresh token if provided (for Calendar sync)
        refresh_token = token.get("refresh_token")
        if refresh_token:
            try:
                AuthService.store_refresh_token(user, refresh_token)
            except Exception as e:
                logger.warning("Failed to store refresh token: %s", str(e))

        logger.info("User %s authenticated successfully, redirecting to chat", user.email)
        flash(f"Bem-vindo(a), {user.display_name or user.email}! 🎉", "success")
        return redirect(url_for("chat.index"))

    except Exception as e:
        logger.error("Callback processing error: %s", str(e), exc_info=True)
        flash("Erro interno ao processar login. Veja os logs.", "error")
        return redirect(url_for("auth.login"))


@auth_bp.route("/logout")
def logout():
    """Log the user out and clear session."""
    if current_user.is_authenticated:
        email = current_user.email
        logout_user()
        logger.info("User %s logged out", email)
    
    # Specifically clear everything but keep the flashes
    session.clear()
    flash("Você saiu com sucesso.", "info")
    
    # Force redirect to login with a flag to prevent auto-return
    return redirect(url_for("auth.login", logged_out=1))


@auth_bp.route("/enable-sync", methods=["POST"])
@login_required
def enable_sync():
    """Request additional Calendar scope and enable sync."""
    redirect_uri = url_for("auth.sync_callback", _external=True)
    extra_scopes = current_app.config["GOOGLE_CALENDAR_EXTRA_SCOPES"]
    all_scopes = current_app.config["GOOGLE_CALENDAR_SCOPES"] + extra_scopes

    return oauth.google.authorize_redirect(
        redirect_uri,
        scope=" ".join(all_scopes),
        access_type="offline",
        prompt="consent",  # Force consent to get refresh_token
    )


@auth_bp.route("/sync-callback")
@login_required
def sync_callback():
    """Handle callback after Calendar scope authorization."""
    try:
        token = oauth.google.authorize_access_token()
    except Exception as e:
        logger.exception("Sync OAuth callback error: %s", str(e))
        flash(f"Erro técnico na sincronização: {str(e)}", "error")
        return redirect(url_for("agenda.index"))

    refresh_token = token.get("refresh_token")
    if refresh_token:
        AuthService.store_refresh_token(current_user, refresh_token)
        flash("Sincronização com Google Calendar habilitada! ✅", "success")
    else:
        flash("Não foi possível obter permissão de sincronização.", "warning")

    return redirect(url_for("agenda.index"))
