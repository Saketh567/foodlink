"""
Client Routes
Client portal and dashboard
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from app.database import query_db
from app.utils.decorators import client_required
from app.models.client_model import get_client_by_user_id, get_client_distributions
from app.utils.qrcode_utils import generate_qr_code_bytes, get_client_qr_data
from app.models import pickup_model

client_bp = Blueprint('client', __name__)

@client_bp.route('/dashboard')
@client_required
def dashboard():
    """Client dashboard"""
    user_id = session.get('user_id')
    client = get_client_by_user_id(user_id)
    
    if not client:
        flash('Client information not found', 'danger')
        return redirect(url_for('auth.logout'))
    
    # Get recent distributions
    distributions = get_client_distributions(client['client_id'])
    
    # Get next pickup info (if any)
    next_pickup = None
    
    return render_template('client/dashboard.html', 
                         client=client, 
                         distributions=distributions,
                         next_pickup=next_pickup)

@client_bp.route('/profile')
@client_required
def profile():
    """Client profile page"""
    user_id = session.get('user_id')
    client = get_client_by_user_id(user_id)
    
    if not client:
        flash('Client information not found', 'danger')
        return redirect(url_for('auth.logout'))
    
    return render_template('client/profile.html', client=client)

@client_bp.route('/update-profile', methods=['POST'])
@client_required
def update_profile():
    """Update client profile"""
    user_id = session.get('user_id')
    client = get_client_by_user_id(user_id)
    
    if not client:
        flash('Client information not found', 'danger')
        return redirect(url_for('client.dashboard'))
    
    # Get form data
    address = request.form.get('address')
    family_size = request.form.get('family_size')
    allergies = request.form.get('allergies', '')
    food_preferences = request.form.get('food_preferences', '')
    
    try:
        query_db(
            '''UPDATE clients SET address = %s, family_size = %s, 
               allergies = %s, food_preferences = %s
               WHERE client_id = %s''',
            (address, family_size, allergies, food_preferences, client['client_id']),
            commit=True
        )
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating profile: {str(e)}', 'danger')
        print(f"Update error: {e}")
    
    return redirect(url_for('client.profile'))

@client_bp.route('/history')
@client_required
def history():
    """View distribution history"""
    user_id = session.get('user_id')
    client = get_client_by_user_id(user_id)
    
    if not client:
        flash('Client information not found', 'danger')
        return redirect(url_for('auth.logout'))
    
    distributions = get_client_distributions(client['client_id'])
    
    return render_template('client/history.html', distributions=distributions)

@client_bp.route('/qr-code')
@client_required
def qr_code():
    """Generate QR code for client number"""
    user_id = session.get('user_id')
    client = get_client_by_user_id(user_id)
    
    if not client or not client.get('client_number'):
        flash('Client number not available', 'danger')
        return redirect(url_for('client.dashboard'))
    
    qr_data = get_client_qr_data(client['client_number'])
    img_bytes = generate_qr_code_bytes(qr_data, size=8, border=2)
    
    return send_file(img_bytes, mimetype='image/png')


@client_bp.route('/pickup', methods=['POST'])
@client_required
def create_pickup():
    """Client submits a food pickup request"""
    user_id = session.get('user_id')
    client = get_client_by_user_id(user_id)

    if not client:
        flash('Client information not found', 'danger')
        return redirect(url_for('auth.logout'))

    inventory_id = request.form.get('inventory_id')
    quantity = request.form.get('quantity')

    try:
        pickup_model.create_pickup(user_id, inventory_id, quantity)
        flash('Pickup request submitted successfully!', 'success')
    except Exception as e:
        flash(f'Error submitting pickup request: {str(e)}', 'danger')

    return redirect(url_for('client.dashboard'))


@client_bp.route('/pickups')
@client_required
def view_pickups():
    """View all pickup requests for the client"""
    user_id = session.get('user_id')
    client = get_client_by_user_id(user_id)

    if not client:
        flash('Client information not found', 'danger')
        return redirect(url_for('auth.logout'))

    pickups = pickup_model.get_pickups_by_user(user_id)

    return render_template('client/pickups.html', pickups=pickups)

