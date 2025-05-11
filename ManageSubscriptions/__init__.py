from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_apscheduler import APScheduler
from ManageSubscriptions.handlers.error_handlers import handle_ratelimit_error,handle_too_large
from flask_limiter.errors import RateLimitExceeded
from ManageSubscriptions.config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy()
mail = Mail()
limiter = Limiter(key_func=get_remote_address, default_limits=[])
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = 'info'
scheduler = APScheduler()

app.register_error_handler(RateLimitExceeded, handle_ratelimit_error)
app.register_error_handler(413, handle_too_large)
db.init_app(app)
mail.init_app(app)
limiter.init_app(app)
login_manager.init_app(app)
scheduler.init_app(app)
scheduler.start()
from ManageSubscriptions.main.routes import main_bp
from ManageSubscriptions.api.routes import api_bp
from ManageSubscriptions.auth.routes import auth_bp
from ManageSubscriptions.dashboards.routes import dashboards_bp
from ManageSubscriptions.forms.routes import forms_bp
from ManageSubscriptions.developers.routes import developers_bp

app.register_blueprint(main_bp)
app.register_blueprint(api_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(dashboards_bp)
app.register_blueprint(forms_bp)
app.register_blueprint(developers_bp)

import ManageSubscriptions.tasks.tasks
