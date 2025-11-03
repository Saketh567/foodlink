"""
Report Model
Report generation queries
"""
from app.database import query_db
from datetime import datetime, timedelta

def get_dashboard_stats():
    """Get dashboard statistics"""
    return {
        'total_clients': query_db(
            'SELECT COUNT(*) as count FROM clients',
            one=True
        )['count'],
        'pending_verifications': query_db(
            'SELECT COUNT(*) as count FROM clients WHERE verification_status = "pending"',
            one=True
        )['count'],
        'verified_clients': query_db(
            'SELECT COUNT(*) as count FROM clients WHERE verification_status = "verified"',
            one=True
        )['count'],
        'active_volunteers': query_db(
            'SELECT COUNT(*) as count FROM users WHERE role = "volunteer" AND is_active = 1',
            one=True
        )['count'],
        'today_donations': query_db(
            'SELECT COALESCE(SUM(weight_kg), 0) as total FROM donations WHERE DATE(donation_date) = CURDATE()',
            one=True
        )['total'],
        'total_donations': query_db(
            'SELECT COALESCE(SUM(weight_kg), 0) as total FROM donations',
            one=True
        )['total'],
        'today_distributions': query_db(
            'SELECT COALESCE(SUM(weight_kg), 0) as total FROM distributions WHERE DATE(distribution_date) = CURDATE()',
            one=True
        )['total']
    }

def get_donation_summary(start_date, end_date):
    """Get donation summary for date range"""
    return query_db(
        '''SELECT 
               DATE(donation_date) as date,
               COUNT(*) as num_donations,
               SUM(weight_kg) as total_weight
           FROM donations
           WHERE DATE(donation_date) BETWEEN %s AND %s
           GROUP BY DATE(donation_date)
           ORDER BY date DESC''',
        (start_date, end_date)
    )

def get_distribution_summary(start_date, end_date):
    """Get distribution summary for date range"""
    return query_db(
        '''SELECT 
               DATE(distribution_date) as date,
               COUNT(*) as num_distributions,
               SUM(weight_kg) as total_weight,
               COUNT(DISTINCT client_id) as unique_clients
           FROM distributions
           WHERE DATE(distribution_date) BETWEEN %s AND %s
           GROUP BY DATE(distribution_date)
           ORDER BY date DESC''',
        (start_date, end_date)
    )

def get_volunteer_performance_report(start_date, end_date):
    """Get volunteer performance report"""
    return query_db(
        '''SELECT 
               u.user_id,
               u.full_name,
               u.email,
               COUNT(DISTINCT DATE(d.donation_date)) as active_days,
               COUNT(d.donation_id) as num_pickups,
               COALESCE(SUM(d.weight_kg), 0) as total_rescued,
               COUNT(dist.distribution_id) as num_distributions,
               COALESCE(SUM(dist.weight_kg), 0) as total_distributed
           FROM users u
           LEFT JOIN donations d ON u.user_id = d.volunteer_id
              AND DATE(d.donation_date) BETWEEN %s AND %s
           LEFT JOIN distributions dist ON u.user_id = dist.volunteer_id
              AND DATE(dist.distribution_date) BETWEEN %s AND %s
           WHERE u.role = "volunteer"
           GROUP BY u.user_id
           ORDER BY total_rescued DESC''',
        (start_date, end_date, start_date, end_date)
    )

def get_client_activity_report(start_date, end_date):
    """Get client activity report"""
    return query_db(
        '''SELECT 
               c.client_id,
               c.client_number,
               u.full_name,
               u.email,
               COUNT(dist.distribution_id) as num_visits,
               COALESCE(SUM(dist.weight_kg), 0) as total_received,
               MAX(dist.distribution_date) as last_visit
           FROM clients c
           JOIN users u ON c.user_id = u.user_id
           LEFT JOIN distributions dist ON c.client_id = dist.client_id
              AND DATE(dist.distribution_date) BETWEEN %s AND %s
           WHERE c.verification_status = "verified"
           GROUP BY c.client_id
           ORDER BY num_visits DESC, last_visit DESC''',
        (start_date, end_date)
    )


