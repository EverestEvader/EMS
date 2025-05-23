import os
import uuid
from datetime import datetime, timedelta
from flask import url_for, flash, current_app, render_template
from werkzeug.utils import secure_filename
from flask_mail import Message
from app import mail, db
from models import Event, EventRegistration, User, EventStatus
import logging

def send_reset_password_email(user):
    token = user.generate_reset_token()
    db.session.commit()
    
    msg = Message('Password Reset Request',
                  recipients=[user.email])
    
    reset_url = url_for('reset_password', token=token, _external=True)
    msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    msg.html = render_template('emails/reset_password.html', reset_url=reset_url, user=user)
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {str(e)}")
        return False

def send_event_confirmation_email(user, event):
    msg = Message('Event Registration Confirmation',
                  recipients=[user.email])
    
    event_url = url_for('event_detail', event_id=event.id, _external=True)
    msg.body = f'''Thank you for registering for {event.name}!

Event Details:
Name: {event.name}
Date: {event.date.strftime('%A, %B %d, %Y at %I:%M %p')}
Venue: {event.venue}

You can view the event details here:
{event_url}

We look forward to seeing you there!
'''
    msg.html = render_template('emails/event_confirmation.html', 
                              event=event, 
                              event_url=event_url, 
                              user=user)
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {str(e)}")
        return False

def send_event_reminder_email(user, event):
    msg = Message(f'Reminder: {event.name} Tomorrow',
                  recipients=[user.email])
    
    event_url = url_for('event_detail', event_id=event.id, _external=True)
    msg.body = f'''This is a reminder that you are registered for {event.name} tomorrow.

Event Details:
Name: {event.name}
Date: {event.date.strftime('%A, %B %d, %Y at %I:%M %p')}
Venue: {event.venue}

You can view the event details here:
{event_url}

We look forward to seeing you there!
'''
    msg.html = render_template('emails/event_reminder.html', 
                              event=event, 
                              event_url=event_url, 
                              user=user)
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {str(e)}")
        return False

def send_event_approval_notification(user, event, is_approved):
    status = "approved" if is_approved else "rejected"
    
    msg = Message(f'Event {status.capitalize()}: {event.name}',
                  recipients=[user.email])
    
    event_url = url_for('event_detail', event_id=event.id, _external=True)
    
    if is_approved:
        msg.body = f'''Your event "{event.name}" has been approved!

You can view the event details here:
{event_url}

Thank you for organizing this event.
'''
    else:
        msg.body = f'''Your event "{event.name}" has been rejected.

Please review your event details and make necessary changes before resubmitting.

You can view the event details here:
{event_url}

If you have any questions, please contact the admin.
'''
    
    msg.html = render_template(f'emails/event_{status}.html', 
                              event=event, 
                              event_url=event_url, 
                              user=user)
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        logging.error(f"Failed to send email: {str(e)}")
        return False

def get_upcoming_events(limit=5, public_only=True):
    query = Event.query.filter(
        Event.date > datetime.utcnow(),
        Event.status == EventStatus.APPROVED
    )
    
    if public_only:
        query = query.filter(Event.is_public == True)
    
    return query.order_by(Event.date.asc()).limit(limit).all()

def get_user_registrations(user_id):
    return EventRegistration.query.filter_by(user_id=user_id).all()

def check_event_reminders():
    """Check for events happening tomorrow and send reminders to registered users"""
    tomorrow = datetime.utcnow().date() + timedelta(days=1)
    tomorrow_start = datetime.combine(tomorrow, datetime.min.time())
    tomorrow_end = datetime.combine(tomorrow, datetime.max.time())
    
    # Find events happening tomorrow
    tomorrow_events = Event.query.filter(
        Event.date >= tomorrow_start,
        Event.date <= tomorrow_end,
        Event.status == EventStatus.APPROVED
    ).all()
    
    for event in tomorrow_events:
        # Get all registered users for this event
        registrations = EventRegistration.query.filter_by(event_id=event.id).all()
        
        for registration in registrations:
            user = User.query.get(registration.user_id)
            if user:
                send_event_reminder_email(user, event)
                
    return len(tomorrow_events)

def get_event_stats_by_creator(creator_id):
    """Get event statistics for a specific creator"""
    events = Event.query.filter_by(creator_id=creator_id).all()
    
    total_events = len(events)
    approved_events = len([e for e in events if e.status == EventStatus.APPROVED])
    pending_events = len([e for e in events if e.status == EventStatus.PENDING])
    cancelled_events = len([e for e in events if e.status == EventStatus.CANCELLED])
    
    upcoming_events = len([e for e in events if e.is_upcoming])
    ongoing_events = len([e for e in events if e.is_ongoing])
    past_events = len([e for e in events if e.is_past])
    
    total_registrations = sum(e.registration_count for e in events)
    
    # Calculate ticket usage
    total_tickets = sum(e.total_tickets for e in events)
    booked_tickets = sum(e.total_tickets - e.available_tickets for e in events)
    
    if total_tickets > 0:
        ticket_usage_rate = (booked_tickets / total_tickets) * 100
    else:
        ticket_usage_rate = 0
    
    return {
        "total_events": total_events,
        "approved_events": approved_events,
        "pending_events": pending_events,
        "cancelled_events": cancelled_events,
        "upcoming_events": upcoming_events,
        "ongoing_events": ongoing_events,
        "past_events": past_events,
        "total_registrations": total_registrations,
        "ticket_usage_rate": ticket_usage_rate,
        "total_tickets": total_tickets,
        "booked_tickets": booked_tickets
    }

def save_logo_file(file):
    """Save an uploaded logo file and return its path
    
    Args:
        file: The uploaded file object
        
    Returns:
        str: The URL path to the saved file or None if there was an error
    """
    if not file:
        return None
        
    try:
        # Get file extension and generate a unique filename
        filename = secure_filename(file.filename)
        if not filename:
            return None
            
        # Add timestamp to make filename unique
        filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
        
        # Define the upload path
        upload_folder = 'static/uploads/logos'
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
            
        # Save the file
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Return the URL path
        return f'/{upload_folder}/{filename}'
    except Exception as e:
        print(f"Error saving logo file: {e}")
        return None


def get_admin_stats():
    """Get overall statistics for admin dashboard"""
    all_events = Event.query.all()
    all_users = User.query.all()
    all_registrations = EventRegistration.query.all()
    
    # User stats
    total_users = len(all_users)
    admin_count = len([u for u in all_users if u.is_admin()])
    creator_count = len([u for u in all_users if u.is_event_creator() and not u.is_admin()])
    attendee_count = len([u for u in all_users if not u.is_event_creator() and not u.is_admin()])
    
    # Event stats
    total_events = len(all_events)
    approved_events = len([e for e in all_events if e.status == EventStatus.APPROVED])
    pending_events = len([e for e in all_events if e.status == EventStatus.PENDING])
    rejected_events = len([e for e in all_events if e.status == EventStatus.REJECTED])
    cancelled_events = len([e for e in all_events if e.status == EventStatus.CANCELLED])
    
    upcoming_events = len([e for e in all_events if e.is_upcoming])
    ongoing_events = len([e for e in all_events if e.is_ongoing])
    past_events = len([e for e in all_events if e.is_past])
    
    # Registration stats
    total_registrations = len(all_registrations)
    
    # Calculate ticket usage
    total_tickets = sum(e.total_tickets for e in all_events)
    booked_tickets = total_tickets - sum(e.available_tickets for e in all_events)
    
    if total_tickets > 0:
        ticket_usage_rate = (booked_tickets / total_tickets) * 100
    else:
        ticket_usage_rate = 0
    
    return {
        "user_stats": {
            "total_users": total_users,
            "admin_count": admin_count,
            "creator_count": creator_count,
            "attendee_count": attendee_count
        },
        "event_stats": {
            "total_events": total_events,
            "approved_events": approved_events,
            "pending_events": pending_events,
            "rejected_events": rejected_events,
            "cancelled_events": cancelled_events,
            "upcoming_events": upcoming_events,
            "ongoing_events": ongoing_events,
            "past_events": past_events
        },
        "registration_stats": {
            "total_registrations": total_registrations,
            "ticket_usage_rate": ticket_usage_rate,
            "total_tickets": total_tickets,
            "booked_tickets": booked_tickets
        },

    }



