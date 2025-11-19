"""
Volunteer Routes
Volunteer operations and dashboard
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app.database import query_db
from app.utils.decorators import volunteer_required
from app.models.donation_model import create_donation, get_donations_by_volunteer
from app.models.volunteer_model import get_volunteer_stats, create_distribution
from app.models.client_model import get_verified_clients, get_client_by_id
from app.utils.qrcode_utils import parse_qr_data
from datetime import datetime

volunteer_bp = Blueprint('volunteer', __name__)

@volunteer_bp.route('/dashboard')
@volunteer_required
def dashboard():
    """Volunteer dashboard"""
    volunteer_id = session.get('user_id')
    
    # Get volunteer statistics
    stats = get_volunteer_stats(volunteer_id)
    
    # Recent donations
    recent_donations = get_donations_by_volunteer(volunteer_id, limit=10)
    
    # Today's pickups
    today_donations = query_db(
        '''SELECT * FROM donations 
           WHERE volunteer_id = %s AND DATE(donation_date) = CURDATE()
           ORDER BY donation_date DESC''',
        (volunteer_id,)
    )
    
    return render_template('volunteer/dashboard.html', 
                          stats=stats, 
                          recent_donations=recent_donations,
                          today_donations=today_donations)

@volunteer_bp.route('/log-pickup', methods=['GET', 'POST'])
@volunteer_required
def log_pickup():
    """Log a food pickup/donation"""
    if request.method == 'POST':
        volunteer_id = session.get('user_id')
        donation_date = request.form.get('donation_date') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        weight_kg = request.form.get('weight_kg')
        food_type = request.form.get('food_type', '')
        source = request.form.get('source', '')
        description = request.form.get('description', '')
        
        try:
            create_donation(
                volunteer_id=volunteer_id,
                donation_date=donation_date,
                weight_kg=float(weight_kg),
                food_type=food_type,
                source=source,
                description=description,
                status='collected'
            )
            flash('Donation logged successfully!', 'success')
            return redirect(url_for('volunteer.dashboard'))
        except Exception as e:
            flash(f'Error logging donation: {str(e)}', 'danger')
            print(f"Donation error: {e}")
    
    return render_template('volunteer/log_pickup.html')

@volunteer_bp.route('/client-signin', methods=['GET', 'POST'])
@volunteer_required
def client_signin():
    """Sign in a client for food distribution"""
    if request.method == 'POST':
        client_number = request.form.get('client_number')
        weight_kg = request.form.get('weight_kg')
        items_description = request.form.get('items_description', '')
        notes = request.form.get('notes', '')
        
        # If QR code data was sent, parse it
        if client_number:
            parsed = parse_qr_data(client_number)
            if parsed:
                client_number = parsed
        
        # Find client by client number
        client = query_db(
            'SELECT client_id, client_number FROM clients WHERE client_number = %s AND verification_status = "verified"',
            (client_number,),
            one=True
        )
        
        if not client:
            flash('Client number not found or not verified', 'danger')
            return render_template('volunteer/client_signin.html')
        
        try:
            volunteer_id = session.get('user_id')
            create_distribution(
                client_id=client['client_id'],
                volunteer_id=volunteer_id,
                distribution_date=datetime.now(),
                weight_kg=float(weight_kg),
                items_description=items_description,
                client_signature=True,
                notes=notes
            )
            flash(f'Client {client["client_number"]} signed in successfully!', 'success')
            return redirect(url_for('volunteer.dashboard'))
        except Exception as e:
            flash(f'Error signing in client: {str(e)}', 'danger')
            print(f"Distribution error: {e}")
    
    return render_template('volunteer/client_signin.html')

@volunteer_bp.route('/verify-qr', methods=['POST'])
@volunteer_required
def verify_qr():
    """API endpoint to verify QR code and return client info"""
    data = request.get_json()
    qr_data = data.get('qr_data', '')
    
    if not qr_data:
        return jsonify({'success': False, 'message': 'No QR data provided'}), 400
    
    # Parse QR code data
    client_number = parse_qr_data(qr_data)
    
    if not client_number:
        return jsonify({'success': False, 'message': 'Invalid QR code format'}), 400
    
    # Get client information
    client = query_db(
        '''SELECT c.client_id, c.client_number, c.photo_path, u.full_name, u.email
           FROM clients c
           JOIN users u ON c.user_id = u.user_id
           WHERE c.client_number = %s AND c.verification_status = "verified"''',
        (client_number,),
        one=True
    )
    
    if not client:
        return jsonify({'success': False, 'message': 'Client not found or not verified'}), 404
    
    return jsonify({
        'success': True,
        'client': {
            'client_number': client['client_number'],
            'full_name': client['full_name'],
            'email': client['email'],
            'photo_path': client.get('photo_path') or None
        }
    }), 200

@volunteer_bp.route('/my-pickups')
@volunteer_required
def my_pickups():
    """View all pickups by this volunteer"""
    volunteer_id = session.get('user_id')
    donations = get_donations_by_volunteer(volunteer_id)
    
    return render_template('volunteer/my_pickups.html', donations=donations)


