import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Define base model class
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

# Configure Flask-Mail - Using file system mail for testing/development
app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "localhost")
app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 25))
app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", "false").lower() == "true"
app.config["MAIL_USE_SSL"] = os.environ.get("MAIL_USE_SSL", "false").lower() == "true"
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@eventhub.com")

# For development, use file system mail
if app.debug:
    app.config["MAIL_SUPPRESS_SEND"] = False
    # Emails will be saved to temp/mails folder in development mode
    import os
    mail_folder = os.path.join(os.getcwd(), 'temp', 'mails')
    if not os.path.exists(mail_folder):
        os.makedirs(mail_folder, exist_ok=True)
    app.config["MAIL_DEFAULT_SENDER"] = "admin@corporateeventhub.com"

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
mail.init_app(app)
csrf.init_app(app)

# Configure login manager
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

# Import models and create tables
with app.app_context():
    import models  # noqa: F401
    from models import User, UserRole
    
    db.create_all()
    logging.info("Database tables created")
    
    # Create default admin account if it doesn't exist
    admin_email = "admin@eventhub.com"
    if not User.query.filter_by(email=admin_email).first():
        admin = User(
            username="admin",
            email=admin_email,
            role=UserRole.ADMIN
        )
        admin.set_password("Admin@123")  # Set a default password
        db.session.add(admin)
        db.session.commit()
        logging.info("Default admin account created")

# Set up error handlers
from flask import render_template

@app.errorhandler(403)
def forbidden(e):
    return render_template("errors/403.html"), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("errors/500.html"), 500
