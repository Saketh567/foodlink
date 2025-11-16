"""
Authentication Routes
Handles login, logout, and registration
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.database import query_db
from app.utils.security import hash_password, verify_password, validate_password, validate_email, validate_phone

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Query user from database
        user = query_db(
            'SELECT * FROM users WHERE email = %s',
            (email,),
            one=True
        )
        
        if user and verify_password(password, user['password_hash']):
            if not user['is_active']:
                flash('Your account is inactive. Please contact an administrator.', 'warning')
                return render_template('auth/login.html')
            
            # Set session variables
            session.permanent = True
            session['user_id'] = user['user_id']
            session['email'] = user['email']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            
            # Redirect based on role
            if user['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user['role'] == 'volunteer':
                return redirect(url_for('volunteer.dashboard'))
            else:
                return redirect(url_for('client.dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Client registration"""
    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        address = request.form.get('address')
        family_size = request.form.get('family_size')
        allergies = request.form.get('allergies', '')
        food_preferences = request.form.get('food_preferences', '')
        
        # Validate inputs
        if not validate_email(email):
            flash('Invalid email format', 'danger')
            return render_template('auth/register.html')
        
        valid, msg = validate_password(password)
        if not valid:
            flash(msg, 'danger')
            return render_template('auth/register.html')
        
        if not validate_phone(phone):
            flash('Invalid phone number format (must be 10 digits)', 'danger')
            return render_template('auth/register.html')
        
        # Check if email already exists
        existing = query_db('SELECT user_id FROM users WHERE email = %s', (email,), one=True)
        if existing:
            flash('Email already registered', 'danger')
            return render_template('auth/register.html')
        
        try:
            # Insert user
            user_id = query_db(
                '''INSERT INTO users (email, password_hash, full_name, phone, role, is_active)
                   VALUES (%s, %s, %s, %s, %s, %s)''',
                (email, hash_password(password), full_name, phone, 'client', 0),
                commit=True
            )
            
            # Insert client details
            query_db(
                '''INSERT INTO clients (user_id, address, family_size, allergies, food_preferences, verification_status)
                   VALUES (%s, %s, %s, %s, %s, %s)''',
                (user_id, address, family_size, allergies, food_preferences, 'pending'),
                commit=True
            )
            
            flash('Registration successful! Please wait for admin verification.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash('Registration failed. Please try again.', 'danger')
            print(f"Registration error: {e}")
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('index'))


