"""Agenda routes — calendar page and events API."""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import render_template, request, jsonify, flash
from flask_login import login_required, current_user

from app.blueprints.agenda import agenda_bp
from app.services.scheduling_service import SchedulingService

logger = logging.getLogger(__name__)


@agenda_bp.route("/")
@login_required
def index():
    """Render agenda/calendar page."""
    return render_template("agenda/calendar.html")


@agenda_bp.route("/events")
@login_required
def events():
    """Return events as JSON for FullCalendar or list view.

    Accepts optional query params:
        start: ISO date string
        end: ISO date string
    """
    try:
        user_tz = current_user.timezone or "America/Sao_Paulo"
        tz = ZoneInfo(user_tz)

        start_str = request.args.get("start")
        end_str = request.args.get("end")

        start_dt = None
        end_dt = None

        if start_str:
            try:
                # 1. Try ISO format (from FullCalendar)
                start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            except ValueError:
                # 2. Fallback to flexible parsing
                start_dt = SchedulingService.parse_datetime_safe(start_str, user_tz)

        if end_str:
            try:
                end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
            except ValueError:
                end_dt = SchedulingService.parse_datetime_safe(end_str, user_tz)

        # Ensure we are comparing aware datetimes against aware column
        if start_dt and start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=tz)
        if end_dt and end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=tz)

        events = SchedulingService.list_events(
            user_id=current_user.id,
            start=start_dt,
            end=end_dt,
        )

        return jsonify([event.to_dict() for event in events])

    except Exception as e:
        logger.error("Error fetching events: %s", str(e), exc_info=True)
        return jsonify([]), 500


@agenda_bp.route("/sync", methods=["POST"])
@login_required
def sync():
    """Manual resync of all user events with Google Calendar."""
    if not current_user.calendar_sync_enabled:
        return jsonify({"success": False, "error": "Sincronização não habilitada"}), 400

    try:
        from app.services.google_calendar_service import GoogleCalendarService

        service = GoogleCalendarService()
        results = service.sync_all_events(current_user)

        return jsonify({
            "success": True,
            "synced": results.get("synced", 0),
            "errors": results.get("errors", 0),
        })

    except Exception as e:
        logger.error("Sync error: %s", str(e), exc_info=True)
        return jsonify({"success": False, "error": "Erro na sincronização"}), 500
