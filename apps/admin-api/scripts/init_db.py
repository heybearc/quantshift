#!/usr/bin/env python3
"""
Initialize database and create admin user.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from core.database import engine, Base, SessionLocal
from core.security import get_password_hash
from models.user import User, UserRole
import uuid

def init_db():
    """Initialize database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")

def create_admin_user(email: str, password: str, full_name: str = "Admin User"):
    """Create admin user."""
    db: Session = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"⚠️  User {email} already exists")
            return
        
        # Create admin user
        admin_user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=get_password_hash(password),
            full_name=full_name,
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"✓ Admin user created: {email}")
        print(f"  ID: {admin_user.id}")
        print(f"  Role: {admin_user.role}")
        
    except Exception as e:
        print(f"✗ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("QuantShift Admin API - Database Initialization")
    print("=" * 60)
    print()
    
    # Initialize database
    init_db()
    print()
    
    # Create admin user
    admin_email = "corya1992@gmail.com"
    admin_password = "admin123"  # Change this in production!
    
    create_admin_user(
        email=admin_email,
        password=admin_password,
        full_name="Cory Anderson"
    )
    
    print()
    print("=" * 60)
    print("Database initialization complete!")
    print("=" * 60)
    print()
    print(f"Admin credentials:")
    print(f"  Email: {admin_email}")
    print(f"  Password: {admin_password}")
    print()
    print("⚠️  IMPORTANT: Change the admin password after first login!")
    print()
