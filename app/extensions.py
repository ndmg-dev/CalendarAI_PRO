"""Flask extensions initialization.

Extensions are instantiated here without binding to a specific app,
following the application factory pattern.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Database ORM
db = SQLAlchemy()

# Authentication / session management
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "info"
