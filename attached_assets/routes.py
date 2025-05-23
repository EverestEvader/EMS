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

            if next_page and next_page.startswith(
                    '/'):  # Ensure the next page is relative
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
        flash('Your registration has been cancelled.', 'success')
    else:
        flash('Cancellation failed. Please try again.', 'danger')

    return redirect(url_for('event_detail', event_id=event_id))


@app.route('/my-events')
@login_required
def user_events():
    registered_events = Event.query.join(EventRegistration).filter(
        EventRegistration.user_id == current_user.id).order_by(
            Event.date.asc()).all()

    return render_template('user_events.html', events=registered_events)


# Dashboard routes
@app.route('/dashboard/creator')
@creator_required
def dashboard_creator():
    stats = get_event_stats_by_creator(current_user.id)

    # Get creator's events
    events = Event.query.filter_by(creator_id=current_user.id).order_by(
        Event.date.desc()).all()

    return render_template('dashboard_creator.html',
                           stats=stats,
                           events=events)


@app.route('/dashboard/admin')
@admin_required
def dashboard_admin():
    stats = get_admin_stats()

    # Get pending events for approval
    pending_events = Event.query.filter_by(
        status=EventStatus.PENDING).order_by(Event.created_at.asc()).all()

    return render_template('dashboard_admin.html',
                           stats=stats,
                           pending_events=pending_events)


# Admin Panel routes
@app.route('/admin')
@admin_required
def admin_panel():
    events = Event.query.order_by(Event.created_at.desc()).all()
    users = User.query.all()

    return render_template('admin_panel.html', events=events, users=users)


@app.route('/admin/events/<int:event_id>/approve', methods=['POST'])
@admin_required
def admin_approve_event(event_id):
    event = Event.query.get_or_404(event_id)
    event.status = EventStatus.APPROVED
    db.session.commit()

    # Notify the event creator
    creator = User.query.get(event.creator_id)
    send_event_approval_notification(creator, event, True)

    flash(f'Event "{event.name}" has been approved.', 'success')
    return redirect(url_for('dashboard_admin'))


@app.route('/admin/events/<int:event_id>/reject', methods=['POST'])
@admin_required
def admin_reject_event(event_id):
    event = Event.query.get_or_404(event_id)
    event.status = EventStatus.REJECTED
    db.session.commit()

    # Notify the event creator
    creator = User.query.get(event.creator_id)
    send_event_approval_notification(creator, event, False)

    flash(f'Event "{event.name}" has been rejected.', 'danger')
    return redirect(url_for('dashboard_admin'))


@app.route('/admin/users/<int:user_id>/role', methods=['POST'])
@admin_required
def admin_change_user_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')

    if new_role in [role.name for role in UserRole]:
        user.role = UserRole[new_role]
        db.session.commit()
        flash(f'User role updated to {user.role.value}.', 'success')
    else:
        flash('Invalid role specified.', 'danger')

    return redirect(url_for('admin_panel'))
