from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from ManageSubscriptions import db,login_manager
from flask_login import UserMixin
import uuid
@login_manager.user_loader
def load_user(user_id):
    return Client.query.get(user_id)

class Client(db.Model,UserMixin):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role = db.Column(db.String(50), default="client")
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    subscription_type = db.Column(db.String(50), default="free")
    remaining_days = db.Column(db.Integer, nullable=True, default=None)
    api_token = db.Column(db.Text, unique=True, nullable=False)
    profile_image = db.Column(db.String(255), nullable=False, default='default.png')
    created_at = db.Column(db.DateTime, default=lambda:datetime.now())
    requests = db.Column(db.Integer, nullable=False, default=0)
    subscribers_limit = db.Column(db.Integer, nullable=False, default=30)
    plans_limit = db.Column(db.Integer, nullable=False, default=1)
    allowed_requests = db.Column(db.Integer, nullable=False, default=200)
    ip_changed_password = db.Column(db.String(20), nullable=True)
    confirmed = db.Column(db.Boolean, nullable=False ,default=False)
    confirmation_token = db.Column(db.String(100), nullable=True, unique=True)
    token_created_at = db.Column(db.DateTime, nullable=True)
    reset_token = db.Column(db.String(100), nullable=True, unique=True)
    reset_token_created_at = db.Column(db.DateTime, nullable=True)
    notified_for_limit = db.Column(db.Boolean, default=False, nullable=False)
    notified_for_expiration = db.Column(db.Boolean, default=False, nullable=False)
    api_logs_chart = db.Column(db.String(255), unique=True, nullable=True)

    plans = db.relationship('ClientPlan', backref='client', lazy=True)
    subscribers = db.relationship('ClientSubscriber', backref='client', lazy=True)


class ClientPlan(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('client.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda:datetime.now())

    subscribers = db.relationship('ClientSubscriber', backref='plan', lazy=True)


class ClientSubscriber(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('client.id'), nullable=False)
    user_id = db.Column(db.String(255), nullable=False)  # external user ID from client's system
    plan_id = db.Column(db.String(36), db.ForeignKey('client_plan.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    remaining_days = db.Column(db.Integer, nullable=False)
    active = db.Column(db.Boolean, default=True)
    meta_data = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda:datetime.now())

class APIUsageTrack(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('client.id'), nullable=False)
    usage_date = db.Column(db.Date, nullable=False, default=datetime.now().date())
    usage_quantity = db.Column(db.Integer, default=1, nullable=False)

    client = db.relationship('Client', backref='api_usage_logs')



class SupportMessages(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.Boolean, default=0, nullable=False)