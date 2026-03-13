"""Google Calendar sync service — push local events to Google Calendar."""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.extensions import db
from app.models.event import Event
from app.models.calendar_sync import CalendarSync
from app.models.user import User
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """Manages synchronization between local events and Google Calendar.

    Direction: Local (Supabase) → Google Calendar (push only in v1).
    Source of truth: Local database.
    """

    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def _get_calendar_service(self, user: User):
        """Build a Google Calendar API service for the given user."""
        refresh_token = AuthService.get_refresh_token(user)
        if not refresh_token:
            raise RuntimeError("Usuário não possui token de sincronização.")

        from flask import current_app

        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=current_app.config["GOOGLE_CLIENT_ID"],
            client_secret=current_app.config["GOOGLE_CLIENT_SECRET"],
            scopes=self.SCOPES,
        )

        return build("calendar", "v3", credentials=credentials)

    def _event_to_google_body(self, event: Event) -> dict:
        """Convert a local Event to Google Calendar event body."""
        body = {
            "summary": event.title,
            "start": {
                "dateTime": event.start_datetime.isoformat(),
                "timeZone": event.timezone,
            },
            "end": {
                "dateTime": event.end_datetime.isoformat(),
                "timeZone": event.timezone,
            },
        }
        if event.description:
            body["description"] = event.description
        return body

    def push_event(self, user: User, event: Event) -> CalendarSync:
        """Push a local event to Google Calendar (create or update).

        Returns the CalendarSync record with updated status.
        """
        try:
            service = self._get_calendar_service(user)
            body = self._event_to_google_body(event)

            # Check if sync record exists
            sync = db.session.query(CalendarSync).filter_by(event_id=event.id).first()

            if sync and sync.google_event_id:
                # Update existing Google Calendar event
                try:
                    result = (
                        service.events()
                        .update(
                            calendarId=sync.google_calendar_id,
                            eventId=sync.google_event_id,
                            body=body,
                        )
                        .execute()
                    )
                    sync.sync_status = "synced"
                    sync.last_synced_at = datetime.now(tz=ZoneInfo("UTC"))
                    sync.etag = result.get("etag")
                    sync.sync_error = None
                    logger.info("Updated Google Calendar event: %s", result.get("id"))
                except HttpError as e:
                    if e.resp.status == 404:
                        # Event was deleted from Google — recreate
                        sync.google_event_id = None
                        return self.push_event(user, event)
                    raise

            else:
                # Create new Google Calendar event
                result = (
                    service.events()
                    .insert(calendarId="primary", body=body)
                    .execute()
                )

                if sync:
                    sync.google_event_id = result.get("id")
                    sync.sync_status = "synced"
                    sync.last_synced_at = datetime.now(tz=ZoneInfo("UTC"))
                    sync.etag = result.get("etag")
                    sync.sync_error = None
                else:
                    sync = CalendarSync(
                        event_id=event.id,
                        user_id=user.id,
                        google_calendar_id="primary",
                        google_event_id=result.get("id"),
                        sync_status="synced",
                        last_synced_at=datetime.now(tz=ZoneInfo("UTC")),
                        etag=result.get("etag"),
                    )
                    db.session.add(sync)

                logger.info("Created Google Calendar event: %s", result.get("id"))

            db.session.commit()
            return sync

        except Exception as e:
            logger.error("Push event error: %s", str(e), exc_info=True)
            # Record the error without corrupting local data
            sync = db.session.query(CalendarSync).filter_by(event_id=event.id).first()
            if not sync:
                sync = CalendarSync(
                    event_id=event.id,
                    user_id=user.id,
                    google_calendar_id="primary",
                    sync_status="error",
                    sync_error=str(e)[:500],
                )
                db.session.add(sync)
            else:
                sync.sync_status = "error"
                sync.sync_error = str(e)[:500]
            db.session.commit()
            return sync

    def delete_event(self, user: User, event: Event) -> None:
        """Delete an event from Google Calendar."""
        sync = db.session.query(CalendarSync).filter_by(event_id=event.id).first()
        if not sync or not sync.google_event_id:
            return

        try:
            service = self._get_calendar_service(user)
            service.events().delete(
                calendarId=sync.google_calendar_id,
                eventId=sync.google_event_id,
            ).execute()

            sync.sync_status = "synced"
            sync.sync_error = None
            sync.last_synced_at = datetime.now(tz=ZoneInfo("UTC"))
            db.session.commit()
            logger.info("Deleted Google Calendar event: %s", sync.google_event_id)

        except HttpError as e:
            if e.resp.status == 404:
                # Already deleted — that's fine
                sync.sync_status = "synced"
                sync.sync_error = None
                db.session.commit()
            else:
                sync.sync_status = "error"
                sync.sync_error = str(e)[:500]
                db.session.commit()
                logger.error("Delete event error: %s", str(e))

    def sync_all_events(self, user: User) -> dict:
        """Resync all active events for a user. Returns counts."""
        if not user.calendar_sync_enabled:
            return {"synced": 0, "errors": 0, "message": "Sync not enabled"}

        events = (
            db.session.query(Event)
            .filter_by(user_id=user.id, status="active")
            .all()
        )

        synced = 0
        errors = 0

        for event in events:
            result = self.push_event(user, event)
            if result.sync_status == "synced":
                synced += 1
            else:
                errors += 1

        # Handle cancelled events — delete from Google
        cancelled_events = (
            db.session.query(Event)
            .filter_by(user_id=user.id, status="cancelled")
            .join(CalendarSync, CalendarSync.event_id == Event.id)
            .filter(CalendarSync.google_event_id.isnot(None))
            .all()
        )

        for event in cancelled_events:
            self.delete_event(user, event)

        logger.info(
            "Sync completed for user %s: %d synced, %d errors",
            user.email, synced, errors,
        )

        return {"synced": synced, "errors": errors}
