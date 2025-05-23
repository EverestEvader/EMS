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
        "analytics": {
            "event_type_breakdown": get_event_type_analytics(),
            "monthly_trends": get_monthly_analytics(),
            "top_performers": get_top_performers(),
            "revenue_analytics": get_revenue_analytics()
        }
    }


def get_event_type_analytics():
    """Get detailed event type analytics"""
    from models import EventType
    type_stats = {}
    for event_type in EventType:
        events = Event.query.filter_by(event_type=event_type).all()
        total_events = len(events)
        approved_events = len([e for e in events if e.status == EventStatus.APPROVED])
        total_capacity = sum(e.total_tickets for e in events)
        total_booked = sum((e.total_tickets - e.available_tickets) for e in events)
        
        type_stats[event_type.value] = {
            'total_events': total_events,
            'approved_events': approved_events,
            'total_capacity': total_capacity,
            'total_booked': total_booked,
            'booking_rate': round((total_booked / max(total_capacity, 1)) * 100, 1),
            'approval_rate': round((approved_events / max(total_events, 1)) * 100, 1)
        }
    return type_stats


def get_monthly_analytics():
    """Get monthly trends for the last 6 months"""
    from datetime import datetime, timedelta
    
    monthly_data = []
    now = datetime.utcnow()
    
    for i in range(6):
        # Calculate month boundaries
        month_start = now.replace(day=1) - timedelta(days=30*i)
        next_month = month_start + timedelta(days=32)
        month_end = next_month.replace(day=1) - timedelta(days=1)
        
        # Get statistics for this month
        users_created = User.query.filter(
            User.created_at >= month_start,
            User.created_at <= month_end
        ).count()
        
        events_created = Event.query.filter(
            Event.created_at >= month_start,
            Event.created_at <= month_end
        ).count()
        
        registrations = EventRegistration.query.filter(
            EventRegistration.registered_at >= month_start,
            EventRegistration.registered_at <= month_end
        ).count()
        
        # Calculate revenue for the month
        month_revenue = 0
        for event in Event.query.filter(
            Event.created_at >= month_start,
            Event.created_at <= month_end,
            Event.is_free == False
        ).all():
            booked = event.total_tickets - event.available_tickets
            month_revenue += event.price * booked
        
        monthly_data.append({
            'month': month_start.strftime('%Y-%m'),
            'month_name': month_start.strftime('%B %Y'),
            'users': users_created,
            'events': events_created,
            'registrations': registrations,
            'revenue': round(month_revenue, 2)
        })
    
    return list(reversed(monthly_data))  # Show chronologically


def get_top_performers():
    """Get top performing events and creators"""
    # Top events by registration rate
    top_events = []
    for event in Event.query.filter(Event.status == EventStatus.APPROVED).all():
        if event.total_tickets > 0:
            booked = event.total_tickets - event.available_tickets
            rate = (booked / event.total_tickets) * 100
            top_events.append({
                'name': event.name,
                'creator': event.creator.username,
                'registration_rate': round(rate, 1),
                'booked_tickets': booked,
                'total_tickets': event.total_tickets,
                'event_type': event.event_type.value
            })
    
    top_events = sorted(top_events, key=lambda x: x['registration_rate'], reverse=True)[:10]
    
    # Top creators by total events and registrations
    creator_stats = {}
    for event in Event.query.all():
        creator_id = event.creator_id
        if creator_id not in creator_stats:
            creator = User.query.get(creator_id)
            creator_stats[creator_id] = {
                'username': creator.username if creator else 'Unknown',
                'total_events': 0,
                'approved_events': 0,
                'total_registrations': 0,
                'total_revenue': 0
            }
        
        stats = creator_stats[creator_id]
        stats['total_events'] += 1
        
        if event.status == EventStatus.APPROVED:
            stats['approved_events'] += 1
            booked = event.total_tickets - event.available_tickets
            stats['total_registrations'] += booked
            
            if not event.is_free:
                stats['total_revenue'] += event.price * booked
    
    top_creators = sorted(creator_stats.values(), key=lambda x: x['total_events'], reverse=True)[:10]
    
    return {
        'events': top_events,
        'creators': top_creators
    }


def get_revenue_analytics():
    """Get detailed revenue analytics"""
    from models import EventType
    total_revenue = 0
    revenue_by_type = {}
    
    # Initialize revenue by type
    for event_type in EventType:
        revenue_by_type[event_type.value] = 0
    
    paid_events = Event.query.filter(Event.is_free == False).all()
    
    for event in paid_events:
        booked = event.total_tickets - event.available_tickets
        event_revenue = event.price * booked
        total_revenue += event_revenue
        revenue_by_type[event.event_type.value] += event_revenue
    
    # Calculate average ticket price
    total_paid_tickets = sum((e.total_tickets - e.available_tickets) for e in paid_events)
    avg_ticket_price = round(total_revenue / max(total_paid_tickets, 1), 2)
    
    return {
        'total_revenue': round(total_revenue, 2),
        'revenue_by_type': {k: round(v, 2) for k, v in revenue_by_type.items()},
        'paid_events_count': len(paid_events),
        'free_events_count': Event.query.filter(Event.is_free == True).count(),
        'avg_ticket_price': avg_ticket_price,
        'total_paid_tickets': total_paid_tickets
    }
