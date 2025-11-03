"""
Security Utilities
Password hashing, validation, and security helper functions
"""
import hashlib
import re
from functools import wraps
from flask import session, redirect, url_for, flash

def hash_password(password):
    """
    Hash password using SHA-256
    For production, consider using bcrypt or argon2
    """
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password, hashed_password):
    """Verify password against hash"""
    return hash_password(plain_password) == hashed_password

def validate_password(password):
    """
    Validate password strength
    Minimum 8 characters, at least one letter and one number
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, "Password is valid"

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number (10 digits)"""
    pattern = r'^\d{10}$'
    return re.match(pattern, phone.replace('-', '').replace(' ', '')) is not None


