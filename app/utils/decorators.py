"""
Custom Decorators
Role-based access control and authentication decorators
"""
from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    """Require user to be logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """Require user to have specific role(s)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page', 'warning')
                return redirect(url_for('auth.login'))
            
            if session.get('role') not in roles:
                flash('You do not have permission to access this page', 'danger')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Require admin role"""
    return role_required('admin')(f)

def volunteer_required(f):
    """Require volunteer role"""
    return role_required('volunteer', 'admin')(f)

def client_required(f):
    """Require client role"""
    return role_required('client')(f)


