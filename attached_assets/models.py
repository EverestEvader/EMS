from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
import uuid
import enum

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Role Enum
class UserRole(enum.Enum):
    ATTENDEE = "attendee"
    EVENT_CREATOR = "event_creator"
    ADMIN = "admin"

# User Model
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.ATTENDEE, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Reset password token
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    created_events = db.relationship('Event', backref='creator', lazy='dynamic')
    registrations = db.relationship('EventRegistration', backref='attendee', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_reset_token(self):
        self.reset_token = str(uuid.uuid4())
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token
    
    def get_upcoming_events(self):
        return Event.query.join(EventRegistration).filter(
            EventRegistration.user_id == self.id,
            Event.date >= datetime.utcnow()
        ).order_by(Event.date.asc()).all()
    
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    def is_event_creator(self):
        return self.role == UserRole.EVENT_CREATOR or self.role == UserRole.ADMIN
    
    def is_attendee(self):
        return self.role == UserRole.ATTENDEE or self.role == UserRole.EVENT_CREATOR or self.role == UserRole.ADMIN

# Event Model
class EventStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class EventType(enum.Enum):
    CONFERENCE = "conference"
    WORKSHOP = "workshop"
    SEMINAR = "seminar"
    NETWORKING = "networking"
    CORPORATE_PARTY = "corporate_party"
    OTHER = "other"

class DressCode(enum.Enum):
    FORMAL = "formal"
    BUSINESS_CASUAL = "business_casual"
    CASUAL = "casual"
    THEMED = "themed"

class EventLocation(enum.Enum):
    INDOOR = "indoor"
    OUTDOOR = "outdoor"
    HYBRID = "hybrid"

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    venue = db.Column(db.String(100), nullable=False)
    event_type = db.Column(db.Enum(EventType), default=EventType.CONFERENCE, nullable=False)
    dress_code = db.Column(db.Enum(DressCode), default=DressCode.BUSINESS_CASUAL, nullable=False)
    location_type = db.Column(db.Enum(EventLocation), default=EventLocation.INDOOR, nullable=False)
    is_public = db.Column(db.Boolean, default=True)
    is_free = db.Column(db.Boolean, default=True)
    price = db.Column(db.Float, default=0.0)
    total_tickets = db.Column(db.Integer, nullable=False)
    available_tickets = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(EventStatus), default=EventStatus.PENDING, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=True)
    logo_url = db.Column(db.String(200), nullable=True)
    company_name = db.Column(db.String(100), nullable=True)
    invitation_only = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    registrations = db.relationship('EventRegistration', backref='event', lazy='dynamic', cascade="all, delete-orphan")
    
    def is_registered(self, user_id):
        return EventRegistration.query.filter_by(event_id=self.id, user_id=user_id).first() is not None
    
    def register_user(self, user_id):
        try:
            if self.available_tickets > 0 and not self.is_registered(user_id):
                registration = EventRegistration()
                registration.event_id = self.id
                registration.user_id = user_id
                db.session.add(registration)
                self.available_tickets -= 1
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            print(f"Error in register_user: {e}")
            return False
    
    def unregister_user(self, user_id):
        try:
            registration = EventRegistration.query.filter_by(event_id=self.id, user_id=user_id).first()
            if registration:
                db.session.delete(registration)
                self.available_tickets += 1
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            print(f"Error in unregister_user: {e}")
            return False
    
    def is_creator(self, user_id):
        return self.creator_id == user_id
    
    @property
    def registration_count(self):
        return self.registrations.count()
    
    @property
    def is_upcoming(self):
        return self.date > datetime.utcnow()
    
    @property
    def is_ongoing(self):
        now = datetime.utcnow()
        return self.date <= now and self.end_date >= now
    
    @property
    def is_past(self):
        return self.end_date < datetime.utcnow()

# Event Registration Model
class EventRegistration(db.Model):
    __tablename__ = 'event_registrations'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('event_id', 'user_id', name='_event_user_uc'),
    )
