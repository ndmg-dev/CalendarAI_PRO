import os
import sys
import logging
import uuid
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["FLASK_APP"] = "wsgi.py"
from config import Config
from app.extensions import db
from app.models.event import Event
from app import create_app

app = create_app()

with app.app_context():
    events = Event.query.all()
    for e in events:
        print(f"ID={e.id}, title={e.title}, start={e.start_datetime}, tz={e.timezone}")
