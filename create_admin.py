#!/usr/bin/env python3
"""
Script to create an admin user for the Event Management System
"""
from app import app, db
from models import User, UserRole
from werkzeug.security import generate_password_hash

def create_admin_user():
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(role=UserRole.ADMIN).first()
        if admin:
            print(f"Admin user already exists: {admin.email}")
            return
        
        # Create admin user
        admin_user = User(
            email='admin@corporateeventhub.com',
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role=UserRole.ADMIN
        )
        
        db.session.add(admin_user)
        db.session.commit()
        
        print("Admin user created successfully!")
        print("Email: admin@corporateeventhub.com")
        print("Password: admin123")
        print("\nPlease change this password after first login!")

if __name__ == '__main__':
    create_admin_user()