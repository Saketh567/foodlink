"""
Donation Model
Donation tracking operations
"""
from app.database import query_db

def create_donation(volunteer_id, donation_date, weight_kg, food_type=None, 
                   source=None, description=None, status='collected'):
    """Create a new donation record"""
    return query_db(
        '''INSERT INTO donations (volunteer_id, donation_date, weight_kg, food_type, source, description, status)
           VALUES (%s, %s, %s, %s, %s, %s, %s)''',
        (volunteer_id, donation_date, weight_kg, food_type, source, description, status),
        commit=True
    )

def get_donation_by_id(donation_id):
    """Get donation by ID"""
    return query_db(
        '''SELECT d.*, u.full_name as volunteer_name
           FROM donations d
           JOIN users u ON d.volunteer_id = u.user_id
           WHERE d.donation_id = %s''',
        (donation_id,),
        one=True
    )

def get_donations_by_volunteer(volunteer_id, limit=None):
    """Get all donations by a volunteer"""
    query = '''SELECT d.*
               FROM donations d
               WHERE d.volunteer_id = %s
               ORDER BY d.donation_date DESC'''
    
    if limit:
        query += f' LIMIT {limit}'
    
    return query_db(query, (volunteer_id,))

def get_recent_donations(limit=10):
    """Get recent donations"""
    return query_db(
        '''SELECT d.*, u.full_name as volunteer_name
           FROM donations d
           JOIN users u ON d.volunteer_id = u.user_id
           ORDER BY d.donation_date DESC
           LIMIT %s''',
        (limit,)
    )

def get_donations_by_date_range(start_date, end_date):
    """Get donations within a date range"""
    return query_db(
        '''SELECT d.*, u.full_name as volunteer_name
           FROM donations d
           JOIN users u ON d.volunteer_id = u.user_id
           WHERE DATE(d.donation_date) BETWEEN %s AND %s
           ORDER BY d.donation_date DESC''',
        (start_date, end_date)
    )

def update_donation_status(donation_id, status):
    """Update donation status"""
    return query_db(
        'UPDATE donations SET status = %s WHERE donation_id = %s',
        (status, donation_id),
        commit=True
    )

def get_donation_statistics(start_date=None, end_date=None):
    """Get donation statistics"""
    if start_date and end_date:
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
    else:
        return query_db(
            '''SELECT 
                   DATE(donation_date) as date,
                   COUNT(*) as num_donations,
                   SUM(weight_kg) as total_weight
               FROM donations
               GROUP BY DATE(donation_date)
               ORDER BY date DESC
               LIMIT 30'''
        )


