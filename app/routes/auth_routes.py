"""
Authentication Routes
Handles login, logout, and registration
"""
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from app.database import query_db
from app.utils.security import hash_password, verify_password, validate_password, validate_email, validate_phone
from app.utils.helpers import allowed_file
from app.models.volunteer_model import create_volunteer_schedule

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
            # Handle photo upload
            photo_path = None
            if 'photo' in request.files:
                photo = request.files['photo']
                if photo and photo.filename and allowed_file(photo.filename):
                    # Create uploads directory if it doesn't exist
                    upload_folder = current_app.config['UPLOAD_FOLDER']
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    # Generate secure filename
                    filename = secure_filename(photo.filename)
                    # Add timestamp to avoid conflicts
                    from datetime import datetime
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    name, ext = os.path.splitext(filename)
                    filename = f"client_photo_{timestamp}_{name}{ext}"
                    
                    # Save file
                    filepath = os.path.join(upload_folder, filename)
                    photo.save(filepath)
                    photo_path = f"uploads/{filename}"
            
            # Insert user
            user_id = query_db(
                '''INSERT INTO users (email, password_hash, full_name, phone, role, is_active)
                   VALUES (%s, %s, %s, %s, %s, %s)''',
                (email, hash_password(password), full_name, phone, 'client', 0),
                commit=True
            )
            
            # Insert client details
            query_db(
                '''INSERT INTO clients (user_id, address, family_size, allergies, food_preferences, verification_status, photo_path)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                (user_id, address, family_size, allergies, food_preferences, 'pending', photo_path),
                commit=True
            )
            
            flash('Registration successful! Please wait for admin verification.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash('Registration failed. Please try again.', 'danger')
            print(f"Registration error: {e}")
    
    return render_template('auth/register.html')

@auth_bp.route('/register/volunteer', methods=['GET', 'POST'])
def register_volunteer():
    """Volunteer registration with availability scheduling"""
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        full_name = request.form.get('full_name') or f"{first_name} {last_name}".strip()
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone')
        address = request.form.get('address')
        availability = request.form.getlist('availability')  # List of selected days
        
        # Validate inputs
        if not full_name or not first_name or not last_name:
            flash('Please provide both first and last name', 'danger')
            return render_template('auth/register_volunteer.html')
        
        if not validate_email(email):
            flash('Invalid email format', 'danger')
            return render_template('auth/register_volunteer.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/register_volunteer.html')
        
        valid, msg = validate_password(password)
        if not valid:
            flash(msg, 'danger')
            return render_template('auth/register_volunteer.html')
        
        if not validate_phone(phone):
            flash('Invalid phone number format (must be 10 digits)', 'danger')
            return render_template('auth/register_volunteer.html')
        
        if not availability:
            flash('Please select at least one day you are available to volunteer', 'danger')
            return render_template('auth/register_volunteer.html')
        
        # Check if email already exists
        existing = query_db('SELECT user_id FROM users WHERE email = %s', (email,), one=True)
        if existing:
            flash('Email already registered', 'danger')
            return render_template('auth/register_volunteer.html')
        
        try:
            # Insert user as volunteer (inactive by default, needs admin approval)
            user_id = query_db(
                '''INSERT INTO users (email, password_hash, full_name, phone, role, is_active)
                   VALUES (%s, %s, %s, %s, %s, %s)''',
                (email, hash_password(password), full_name, phone, 'volunteer', 0),
                commit=True
            )
            
            # Create schedules for the next 8 weeks based on availability
            # Map day names to weekday numbers (Monday=0, Tuesday=1, etc.)
            day_map = {
                'monday': 0,
                'tuesday': 1,
                'wednesday': 2,
                'thursday': 3,
                'friday': 4
            }
            
            # Standard time slot: 11:00 AM - 2:00 PM
            start_time = '11:00:00'
            end_time = '14:00:00'
            
            # Get today's date
            today = datetime.now().date()
            # Start from next Monday (or today if it's Monday)
            days_until_monday = (7 - today.weekday()) % 7
            if days_until_monday == 0 and today.weekday() == 0:
                start_date = today
            else:
                start_date = today + timedelta(days=days_until_monday)
            
            # Create schedules for 8 weeks
            schedules_created = 0
            for week in range(8):
                for day_name in availability:
                    if day_name.lower() in day_map:
                        weekday = day_map[day_name.lower()]
                        schedule_date = start_date + timedelta(days=(week * 7) + weekday)
                        
                        # Create schedule
                        create_volunteer_schedule(
                            volunteer_id=user_id,
                            schedule_date=schedule_date,
                            start_time=start_time,
                            end_time=end_time,
                            status='scheduled',
                            notes=f'Recurring availability - {day_name.capitalize()}'
                        )
                        schedules_created += 1
            
            flash(f'Registration successful! {schedules_created} availability slots created. Please wait for admin approval to activate your account.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash('Registration failed. Please try again.', 'danger')
            print(f"Volunteer registration error: {e}")
            import traceback
            traceback.print_exc()
    
    return render_template('auth/register_volunteer.html')

@auth_bp.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('index'))


