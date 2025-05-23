from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, IntegerField, FloatField, DateTimeField, RadioField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange, Optional
from models import User, EventType, DressCode, EventLocation, UserRole
import datetime

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    role = RadioField('Choose your role', 
        choices=[
            (UserRole.ATTENDEE.name, 'Attendee - Register for events'),
            (UserRole.EVENT_CREATOR.name, 'Event Creator - Create and manage events')
        ],
        default=UserRole.ATTENDEE.name,
        validators=[DataRequired()]
    )
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email or login.')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Reset Password')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('No account found with that email.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Reset Password')

class EventForm(FlaskForm):
    name = StringField('Event Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    date = DateTimeField('Start Date & Time', validators=[DataRequired()], format='%Y-%m-%d %H:%M', default=datetime.datetime.now() + datetime.timedelta(days=1))
    end_date = DateTimeField('End Date & Time', validators=[DataRequired()], format='%Y-%m-%d %H:%M', default=datetime.datetime.now() + datetime.timedelta(days=1, hours=2))
    venue = StringField('Venue', validators=[DataRequired(), Length(max=100)])
    event_type = SelectField('Event Type', choices=[(event_type.name, event_type.value) for event_type in EventType], validators=[DataRequired()])
    dress_code = SelectField('Dress Code', choices=[(dress_code.name, dress_code.value) for dress_code in DressCode], validators=[DataRequired()])
    location_type = SelectField('Location Type', choices=[(location_type.name, location_type.value) for location_type in EventLocation], validators=[DataRequired()])
    
    # Company information
    company_name = StringField('Company/Organization Name', validators=[Optional(), Length(max=100)])
    logo_file = FileField('Company/Event Logo', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'svg'], 'Images only! (.jpg, .png, .gif, .svg)')
    ])
    logo_url = StringField('or Logo URL', validators=[Optional(), Length(max=200)])
    
    # Event access settings
    is_public = BooleanField('Public Event', default=True)
    invitation_only = BooleanField('Invitation Only', default=False, description='Only specific individuals can register')
    
    # Ticketing
    is_free = BooleanField('Free Entry', default=True)
    price = FloatField('Price (if not free)', validators=[Optional(), NumberRange(min=0)], default=0)
    total_tickets = IntegerField('Total Tickets', validators=[DataRequired(), NumberRange(min=1)], default=100)
    
    # Contact information
    contact_phone = StringField('Contact Phone', validators=[Optional(), Length(max=20)])
    
    submit = SubmitField('Create Event')
    
    def validate_end_date(self, end_date):
        if end_date.data and self.date.data and end_date.data <= self.date.data:
            raise ValidationError('End date must be after start date.')
        
    def validate_price(self, price):
        if not self.is_free.data and (price.data is None or price.data <= 0):
            raise ValidationError('Price must be greater than 0 for paid events.')
    
    def validate_invitation_only(self, invitation_only):
        if invitation_only.data and self.is_public and self.is_public.data:
            raise ValidationError('Invitation-only events must be private (not public).')
