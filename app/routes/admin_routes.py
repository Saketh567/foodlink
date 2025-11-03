"""
Admin Routes
Dashboard, user management, verification, and reports
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.database import query_db
from app.utils.decorators import admin_required
from app.models.report_model import get_dashboard_stats, get_donation_summary, get_volunteer_performance_report
from app.models.client_model import get_pending_clients
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard with statistics"""
    stats = get_dashboard_stats()
    
    # Recent donations
    recent_donations = query_db(
        '''SELECT d.*, u.full_name as volunteer_name
           FROM donations d
           JOIN users u ON d.volunteer_id = u.user_id
           ORDER BY d.donation_date DESC
           LIMIT 10'''
    )
    
    return render_template('admin/dashboard.html', stats=stats, recent_donations=recent_donations)

@admin_bp.route('/verify-clients')
@admin_required
def verify_clients():
    """List pending client verifications"""
    pending_clients = get_pending_clients()
    return render_template('admin/verify_clients.html', clients=pending_clients)

@admin_bp.route('/verify-client/<int:client_id>', methods=['GET', 'POST'])
@admin_required
def verify_client(client_id):
    """Verify a client and assign client number"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'approve':
            # Get location for client number
            location_code = request.form.get('location_code', 'FL')
            
            # Get next client number for this location
            last_client = query_db(
                'SELECT client_number FROM clients WHERE client_number LIKE %s ORDER BY client_number DESC LIMIT 1',
                (f'{location_code}-%',),
                one=True
            )
            
            if last_client:
                try:
                    last_num = int(last_client['client_number'].split('-')[1])
                    next_num = last_num + 1
                except:
                    next_num = 1
            else:
                next_num = 1
            
            client_number = f'{location_code}-{next_num:03d}'
            
            # Get user_id for this client
            client = query_db('SELECT user_id FROM clients WHERE client_id = %s', (client_id,), one=True)
            
            if client:
                # Update client
                query_db(
                    '''UPDATE clients SET verification_status = "verified", 
                       client_number = %s, verified_date = NOW(), verified_by = %s
                       WHERE client_id = %s''',
                    (client_number, session.get('user_id'), client_id),
                    commit=True
                )
                
                # Activate user account
                query_db(
                    'UPDATE users SET is_active = 1 WHERE user_id = %s',
                    (client['user_id'],),
                    commit=True
                )
                
                flash(f'Client verified successfully! Client Number: {client_number}', 'success')
        
        elif action == 'reject':
            reason = request.form.get('reason', 'Incomplete information')
            query_db(
                'UPDATE clients SET verification_status = "rejected", notes = %s WHERE client_id = %s',
                (reason, client_id),
                commit=True
            )
            flash(f'Client verification rejected: {reason}', 'info')
        
        return redirect(url_for('admin.verify_clients'))
    
    # GET request - show client details
    client = query_db(
        '''SELECT c.*, u.full_name, u.email, u.phone, u.created_at
           FROM clients c
           JOIN users u ON c.user_id = u.user_id
           WHERE c.client_id = %s''',
        (client_id,),
        one=True
    )
    
    if not client:
        flash('Client not found', 'danger')
        return redirect(url_for('admin.verify_clients'))
    
    return render_template('admin/verify_clients.html', client=client)

@admin_bp.route('/manage-users')
@admin_required
def manage_users():
    """Manage all users"""
    users = query_db(
        '''SELECT u.*, 
                  CASE WHEN u.role = 'client' THEN c.verification_status ELSE NULL END as verification_status,
                  CASE WHEN u.role = 'client' THEN c.client_number ELSE NULL END as client_number
           FROM users u
           LEFT JOIN clients c ON u.user_id = c.user_id
           ORDER BY u.created_at DESC'''
    )
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/reports')
@admin_required
def reports():
    """Generate and view reports"""
    # Get date range from query params
    start_date = request.args.get('start_date', datetime.now().strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Donation summary
    donation_summary = get_donation_summary(start_date, end_date)
    
    # Volunteer activity
    volunteer_activity = get_volunteer_performance_report(start_date, end_date)
    
    return render_template('admin/reports.html',
                          donation_summary=donation_summary,
                          volunteer_activity=volunteer_activity,
                          start_date=start_date,
                          end_date=end_date)


