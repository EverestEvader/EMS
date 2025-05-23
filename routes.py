import logging
from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from models import User, Event, EventRegistration, UserRole, EventStatus, EventType, DressCode, EventLocation
from forms import LoginForm, SignupForm, ForgotPasswordForm, ResetPasswordForm, EventForm
from utils import (send_reset_password_email, send_event_confirmation_email,
                   get_upcoming_events, get_user_registrations,
                   send_event_approval_notification,
                   get_event_stats_by_creator, get_admin_stats,
                   save_logo_file)


# Decorator for admin-only routes
def admin_required(func):
    @login_required
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin():
            abort(403)
        return func(*args, **kwargs)
    decorated_view.__name__ = func.__name__
    return decorated_view


# Decorator for event-creator-only routes
def creator_required(func):
    @login_required
    def decorated_view(*args, **kwargs):
        if not current_user.is_event_creator():
            abort(403)
        return func(*args, **kwargs)
    decorated_view.__name__ = func.__name__
    return decorated_view


# Base/Landing Page
@app.route('/')
def index():
    upcoming_events = get_upcoming_events(limit=6)
    return render_template('index.html', events=upcoming_events)


# Home Page (requires login)
@app.route('/home')
@login_required
def home():
    now = datetime.now()
    upcoming_events = get_upcoming_events(limit=10)
    user_registrations = current_user.registrations.all()
    registered_events = [reg.event for reg in user_registrations]

    return render_template('home.html',
                           upcoming_events=upcoming_events,
                           registered_events=registered_events,
                           now=now)


# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next', '')

            if next_page and next_page.startswith('/'):
                return redirect(next_page)

            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html', form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = SignupForm()
    
    # Pre-select role based on the URL parameter
    selected_role = request.args.get('role')
    if selected_role in [role.name for role in UserRole] and request.method == 'GET':
        form.role.data = selected_role

    if form.validate_on_submit():
        user = User(username=form.username.data,
                    email=form.email.data,
                    role=UserRole[form.role.data])
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if send_reset_password_email(user):
                flash(
                    'Password reset instructions have been sent to your email.',
                    'info')
            else:
                flash('Failed to send email. Please try again later.',
                      'danger')
        else:
            flash('No account found with that email.', 'danger')

        # Redirect regardless of whether email exists to prevent email enumeration
        return redirect(url_for('login'))

    return render_template('forgot_password.html', form=form)


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    user = User.query.filter_by(reset_token=token).first()

    if not user or user.reset_token_expiry < datetime.utcnow():
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()

        flash('Your password has been reset! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', form=form)


# Event routes
@app.route('/events')
def event_list():
    events = Event.query.filter_by(is_public=True,
                                   status=EventStatus.APPROVED).order_by(
                                       Event.date.asc()).all()

    return render_template('event_list.html', events=events)


@app.route('/events/<int:event_id>')
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)

    # If event is not public or not approved, only creator and admin can view
    if (not event.is_public or event.status != EventStatus.APPROVED) and (
            not current_user.is_authenticated or
        (not current_user.is_admin() and current_user.id != event.creator_id)):
        abort(404)

    is_registered = False
    if current_user.is_authenticated:
        is_registered = event.is_registered(current_user.id)

    return render_template('event_detail.html',
                           event=event,
                           is_registered=is_registered)


@app.route('/events/create', methods=['GET', 'POST'])
@creator_required
def event_create():
    form = EventForm()

    if form.validate_on_submit():
        # Ensure invitation-only events are automatically set to private
        if form.invitation_only.data:
            form.is_public.data = False
            
        # Handle logo file upload if provided
        logo_url = form.logo_url.data
        if form.logo_file.data:
            uploaded_logo_url = save_logo_file(form.logo_file.data)
            if uploaded_logo_url:
                logo_url = uploaded_logo_url
                
        # Create event instance
        event = Event()
        event.name = form.name.data
        event.description = form.description.data
        event.date = form.date.data
        event.end_date = form.end_date.data
        event.venue = form.venue.data
        event.event_type = EventType[form.event_type.data]
        event.dress_code = DressCode[form.dress_code.data]
        event.location_type = EventLocation[form.location_type.data]
        event.is_public = form.is_public.data
        event.is_free = form.is_free.data
        event.price = form.price.data if not form.is_free.data else 0
        event.total_tickets = form.total_tickets.data
        event.available_tickets = form.total_tickets.data
        event.creator_id = current_user.id
        event.contact_phone = form.contact_phone.data
        event.company_name = form.company_name.data
        event.logo_url = logo_url
        event.invitation_only = form.invitation_only.data

        db.session.add(event)
        db.session.commit()

        flash('Event created successfully! It is now pending admin approval.',
              'success')
        return redirect(url_for('dashboard_creator'))

    return render_template('event_create.html', form=form)


@app.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@creator_required
def event_edit(event_id):
    event = Event.query.get_or_404(event_id)

    # Only creator or admin can edit
    if not current_user.is_admin() and current_user.id != event.creator_id:
        abort(403)

    form = EventForm(obj=event)

    if form.validate_on_submit():
        # Ensure invitation-only events are automatically set to private
        if form.invitation_only.data:
            form.is_public.data = False
            
        # Handle logo file upload if provided
        if form.logo_file.data:
            uploaded_logo_url = save_logo_file(form.logo_file.data)
            if uploaded_logo_url:
                form.logo_url.data = uploaded_logo_url
            
        # Update basic fields
        form.populate_obj(event)
        
        # Update enum fields manually
        event.event_type = EventType[form.event_type.data]
        event.dress_code = DressCode[form.dress_code.data]
        event.location_type = EventLocation[form.location_type.data]

        # Handle free events
        if event.is_free:
            event.price = 0

        # Handle ticket changes
        # If tickets were increased, update available tickets accordingly
        ticket_diff = form.total_tickets.data - event.total_tickets
        if ticket_diff > 0:
            event.available_tickets += ticket_diff
        elif ticket_diff < 0 and event.available_tickets > abs(ticket_diff):
            # Ensure we don't reduce below registered users
            event.available_tickets += ticket_diff

        event.total_tickets = form.total_tickets.data

        # Set status back to pending if event was modified after approval
        if event.status == EventStatus.APPROVED:
            event.status = EventStatus.PENDING
            flash(
                'Your event has been updated and will need to be re-approved by an admin.',
                'info')

        db.session.commit()
        flash('Event updated successfully!', 'success')

        if current_user.is_admin():
            return redirect(url_for('admin_panel'))
        else:
            return redirect(url_for('dashboard_creator'))

    # Pre-select the current enum values in the form
    form.event_type.data = event.event_type.name
    form.dress_code.data = event.dress_code.name
    form.location_type.data = event.location_type.name

    return render_template('event_create.html',
                           form=form,
                           event=event,
                           is_edit=True)


@app.route('/events/<int:event_id>/delete', methods=['POST'])
@creator_required
def event_delete(event_id):
    event = Event.query.get_or_404(event_id)

    # Only creator or admin can delete
    if not current_user.is_admin() and current_user.id != event.creator_id:
        abort(403)

    db.session.delete(event)
    db.session.commit()

    flash('Event deleted successfully!', 'success')

    if current_user.is_admin():
        return redirect(url_for('admin_panel'))
    else:
        return redirect(url_for('dashboard_creator'))


# Event Registration routes
@app.route('/events/<int:event_id>/register', methods=['POST'])
@login_required
def event_register(event_id):
    event = Event.query.get_or_404(event_id)

    # Check if event is approved and has available tickets
    if event.status != EventStatus.APPROVED:
        flash('This event is not available for registration.', 'danger')
        return redirect(url_for('event_detail', event_id=event_id))

    if event.available_tickets <= 0:
        flash('Sorry, this event is fully booked.', 'danger')
        return redirect(url_for('event_detail', event_id=event_id))

    # Check if user is already registered
    if event.is_registered(current_user.id):
        flash('You are already registered for this event.', 'info')
        return redirect(url_for('event_detail', event_id=event_id))

    # Register user
    if event.register_user(current_user.id):
        # Send confirmation email
        send_event_confirmation_email(current_user, event)
        flash('Registration successful! A confirmation email has been sent.',
              'success')
    else:
        flash('Registration failed. Please try again.', 'danger')

    return redirect(url_for('event_detail', event_id=event_id))


@app.route('/events/<int:event_id>/unregister', methods=['POST'])
@login_required
def event_unregister(event_id):
    event = Event.query.get_or_404(event_id)

    # Check if user is registered
    if not event.is_registered(current_user.id):
        flash('You are not registered for this event.', 'info')
        return redirect(url_for('event_detail', event_id=event_id))

    # Unregister user
    if event.unregister_user(current_user.id):
        flash('You have been unregistered from this event.', 'success')
    else:
        flash('Unregistration failed. Please try again.', 'danger')

    return redirect(url_for('event_detail', event_id=event_id))


# Dashboard routes
@app.route('/dashboard/creator')
@creator_required
def dashboard_creator():
    # Get user's events
    user_events = Event.query.filter_by(creator_id=current_user.id).order_by(
        Event.created_at.desc()).all()

    # Get statistics
    stats = get_event_stats_by_creator(current_user.id)

    return render_template('dashboard_creator.html',
                           events=user_events,
                           stats=stats)


@app.route('/admin')
@admin_required
def admin_panel():
    # Get all events for admin review
    events = Event.query.order_by(Event.created_at.desc()).all()

    # Get statistics with error handling
    try:
        stats = get_admin_stats()
    except Exception as e:
        print(f"Error in analytics: {e}")
        # Fallback to basic stats
        stats = {
            "user_stats": {
                "total_users": User.query.count(),
                "admin_count": User.query.filter_by(role=UserRole.ADMIN).count(),
                "creator_count": User.query.filter_by(role=UserRole.EVENT_CREATOR).count(), 
                "attendee_count": User.query.filter_by(role=UserRole.ATTENDEE).count()
            },
            "event_stats": {
                "total_events": Event.query.count(),
                "approved_events": Event.query.filter_by(status=EventStatus.APPROVED).count(),
                "pending_events": Event.query.filter_by(status=EventStatus.PENDING).count(),
                "rejected_events": Event.query.filter_by(status=EventStatus.REJECTED).count(),
                "cancelled_events": Event.query.filter_by(status=EventStatus.CANCELLED).count(),
                "upcoming_events": 0,
                "ongoing_events": 0,
                "past_events": 0
            },
            "registration_stats": {
                "total_registrations": EventRegistration.query.count(),
                "ticket_usage_rate": 0,
                "total_tickets": 0,
                "booked_tickets": 0
            },
            "analytics": {
                "event_type_breakdown": {},
                "monthly_trends": [],
                "top_performers": {"events": [], "creators": []},
                "revenue_analytics": {"total_revenue": 0, "total_paid_tickets": 0, "avg_ticket_price": 0, "paid_events_count": 0, "free_events_count": 0}
            }
        }

    return render_template('admin_panel.html', events=events, stats=stats)


@app.route('/admin/events/<int:event_id>/approve', methods=['POST'])
@admin_required
def admin_approve_event(event_id):
    event = Event.query.get_or_404(event_id)
    event.status = EventStatus.APPROVED
    db.session.commit()

    # Send approval notification
    send_event_approval_notification(event.creator, event, True)

    flash(f'Event "{event.name}" has been approved.', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/events/<int:event_id>/reject', methods=['POST'])
@admin_required
def admin_reject_event(event_id):
    event = Event.query.get_or_404(event_id)
    event.status = EventStatus.REJECTED
    db.session.commit()

    # Send rejection notification
    send_event_approval_notification(event.creator, event, False)

    flash(f'Event "{event.name}" has been rejected.', 'warning')
    return redirect(url_for('admin_panel'))


# Profile route
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


# API routes for AJAX calls
@app.route('/api/events/<int:event_id>/registration-status')
@login_required
def api_event_registration_status(event_id):
    event = Event.query.get_or_404(event_id)
    is_registered = event.is_registered(current_user.id)
    
    return jsonify({
        'is_registered': is_registered,
        'available_tickets': event.available_tickets,
        'registration_count': event.registration_count
    })
