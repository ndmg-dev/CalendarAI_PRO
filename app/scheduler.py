"""Background scheduler — checking for upcoming events and sending reminders."""

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app

from app.extensions import db
from app.models.event import Event
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

def check_upcoming_events(app):
    """
    Check for active events starting in the next 30 minutes 
    that haven't had a reminder sent yet.
    """
    with app.app_context():
        # Current time in UTC (events are stored with TZ)
        now = datetime.now(ZoneInfo("UTC"))
        lookahead = now + timedelta(minutes=30)
        
        logger.debug("Checking for events between %s and %s", now, lookahead)
        
        # Find active events starting soon
        upcoming_events = Event.query.filter(
            Event.status == "active",
            Event.notification_sent == False,
            Event.start_datetime > now,
            Event.start_datetime <= lookahead
        ).all()
        
        if not upcoming_events:
            return
            
        logger.info("Found %d upcoming events for notifications", len(upcoming_events))
        
        for event in upcoming_events:
            try:
                user = event.user
                if not user or not user.email:
                    logger.warning("Event %s has no user email, skipping notification", event.id)
                    continue
                
                # Format start time for email (human readable)
                # Convert to user timezone if possible
                tz = ZoneInfo(user.timezone or "America/Sao_Paulo")
                local_start = event.start_datetime.astimezone(tz)
                start_str = local_start.strftime("%H:%M (%d/%m)")
                
                success = EmailService.send_event_reminder(
                    user_email=user.email,
                    user_name=user.display_name or user.email,
                    event_title=event.title,
                    event_start_str=start_str
                )
                
                if success:
                    event.notification_sent = True
                    db.session.commit()
                    logger.info("Reminder sent for event: %s", event.title)
                
            except Exception as e:
                logger.error("Error processing reminder for event %s: %s", event.id, str(e))
                db.session.rollback()

def init_scheduler(app):
    """Initialize APScheduler and register jobs."""
    scheduler = BackgroundScheduler()
    
    # Run every 15 minutes
    scheduler.add_job(
        func=check_upcoming_events,
        trigger="interval",
        minutes=15,
        args=[app],
        id="check_upcoming_events",
        name="Check for upcoming events every 15m",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Event reminder scheduler started (interval: 15m)")
    return scheduler
