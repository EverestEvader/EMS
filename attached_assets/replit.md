# Corporate Event Hub - replit.md

## Overview

Corporate Event Hub is a Flask-based web application for managing corporate events. The system supports three user roles (Admin, Event Creator, and Attendee) with role-based access control and comprehensive event management capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python 3.11)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Flask-Login with session management
- **Email**: Flask-Mail for notifications and password reset
- **Forms**: Flask-WTF with CSRF protection
- **File Handling**: Werkzeug for secure file uploads (event logos)

### Frontend Architecture
- **Templates**: Jinja2 templating engine
- **Styling**: Bootstrap 5 with custom CSS
- **Theme**: Dark theme with responsive design
- **Icons**: Font Awesome for UI elements

### Database Schema
The application uses the following main models:
- **User**: Stores user accounts with role-based permissions
- **Event**: Contains event details, status, and metadata
- **EventRegistration**: Manages user registrations for events
- **Enums**: UserRole, EventStatus, EventType, DressCode, EventLocation

## Key Components

### Authentication System
- User registration with email validation
- Secure password hashing using Werkzeug
- Password reset functionality with token-based email verification
- Role-based access control with decorators
- Session management with "remember me" functionality

### Event Management
- Event creation with comprehensive details (name, description, dates, venue, type, dress code)
- Event status workflow (pending, approved, rejected, cancelled, expired)
- File upload support for event logos
- Event registration system with capacity management
- Admin approval workflow for events

### Email Notifications
- Welcome emails for new registrations
- Event confirmation emails
- Password reset emails
- Event approval/rejection notifications
- Event reminder emails

### User Roles & Permissions
- **Admin**: Full system access, event approval, user management, analytics
- **Event Creator**: Create/manage own events, view creator dashboard
- **Attendee**: Browse events, register for events, view personal dashboard

## Data Flow

1. **User Registration**: New users sign up → Email validation → Account creation → Redirect to login
2. **Event Creation**: Creator submits event → Admin approval required → Email notification → Event goes live
3. **Event Registration**: Attendee browses events → Registration → Confirmation email → Dashboard update
4. **Event Management**: Automated cleanup of expired events via scheduled tasks

## External Dependencies

### Required Services
- **PostgreSQL Database**: Primary data storage
- **SMTP Server**: Email delivery (configurable for production/development)
- **File Storage**: Local filesystem for uploaded logos

### Python Packages
- Flask ecosystem (Flask, Flask-SQLAlchemy, Flask-Login, Flask-Mail, Flask-WTF)
- Database: psycopg2-binary for PostgreSQL connectivity
- Security: Werkzeug for password hashing and file handling
- Forms: WTForms for form validation
- Email: Optional SendGrid integration
- Server: Gunicorn for production deployment

## Deployment Strategy

### Development
- Local development server with Flask debug mode
- File-based email backend for testing
- SQLite fallback option available

### Production
- **Server**: Gunicorn WSGI server
- **Deployment**: Replit autoscale deployment target
- **Database**: PostgreSQL with connection pooling
- **Static Files**: Served via Flask with CDN integration for Bootstrap/FontAwesome
- **Security**: CSRF protection, secure session handling, ProxyFix for reverse proxy

### Environment Configuration
- Database URL via DATABASE_URL environment variable
- Email configuration via MAIL_* environment variables
- Session secret via SESSION_SECRET environment variable
- File upload limits and directory configuration

### Maintenance
- Automated cleanup script for expired events
- Database connection pooling with pre-ping health checks
- Logging configuration for debugging and monitoring
- Error handling with custom error pages (403, 404, 500)

## Key Features

- **Responsive Design**: Mobile-friendly interface with Bootstrap
- **Security**: Password hashing, CSRF protection, role-based access
- **File Uploads**: Secure logo upload with validation
- **Email Integration**: Comprehensive notification system
- **Analytics**: Dashboard views for different user roles
- **Event Lifecycle**: Complete workflow from creation to completion
- **User Experience**: Flash messages, form validation, intuitive navigation