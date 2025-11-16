"""
Volunteer Model
Volunteer activity tracking
"""
from app.database import query_db

def get_volunteer_stats(volunteer_id, start_date=None, end_date=None):
    """Get volunteer statistics"""
    if start_date and end_date:
        return query_db(
            '''SELECT 
                   COUNT(d.donation_id) as num_pickups,
                   COALESCE(SUM(d.weight_kg), 0) as total_rescued,
                   COUNT(DISTINCT DATE(d.donation_date)) as active_days
               FROM users u
               LEFT JOIN donations d ON u.user_id = d.volunteer_id
                  AND DATE(d.donation_date) BETWEEN %s AND %s
               WHERE u.user_id = %s AND u.role = "volunteer"''',
            (start_date, end_date, volunteer_id),
            one=True
        )
    else:
        return query_db(
            '''SELECT 
                   COUNT(d.donation_id) as num_pickups,
                   COALESCE(SUM(d.weight_kg), 0) as total_rescued,
                   COUNT(DISTINCT DATE(d.donation_date)) as active_days
               FROM users u
               LEFT JOIN donations d ON u.user_id = d.volunteer_id
               WHERE u.user_id = %s AND u.role = "volunteer"''',
            (volunteer_id,),
            one=True
        )

def get_all_volunteers_activity(start_date=None, end_date=None):
    """Get activity for all volunteers"""
    if start_date and end_date:
        return query_db(
            '''SELECT 
                   u.user_id,
                   u.full_name,
                   COUNT(d.donation_id) as num_pickups,
                   COALESCE(SUM(d.weight_kg), 0) as total_rescued
               FROM users u
               LEFT JOIN donations d ON u.user_id = d.volunteer_id
                  AND DATE(d.donation_date) BETWEEN %s AND %s
               WHERE u.role = "volunteer"
               GROUP BY u.user_id
               ORDER BY total_rescued DESC''',
            (start_date, end_date)
        )
    else:
        return query_db(
            '''SELECT 
                   u.user_id,
                   u.full_name,
                   COUNT(d.donation_id) as num_pickups,
                   COALESCE(SUM(d.weight_kg), 0) as total_rescued
               FROM users u
               LEFT JOIN donations d ON u.user_id = d.volunteer_id
               WHERE u.role = "volunteer"
               GROUP BY u.user_id
               ORDER BY total_rescued DESC'''
        )

def create_volunteer_schedule(volunteer_id, schedule_date, start_time, end_time, status='scheduled', notes=''):
    """Create a volunteer schedule"""
    return query_db(
        '''INSERT INTO volunteer_schedules (volunteer_id, schedule_date, start_time, end_time, status, notes)
           VALUES (%s, %s, %s, %s, %s, %s)''',
        (volunteer_id, schedule_date, start_time, end_time, status, notes),
        commit=True
    )

def get_volunteer_schedules(volunteer_id, start_date=None, end_date=None):
    """Get volunteer schedules"""
    if start_date and end_date:
        return query_db(
            '''SELECT * FROM volunteer_schedules
               WHERE volunteer_id = %s
                 AND schedule_date BETWEEN %s AND %s
               ORDER BY schedule_date, start_time''',
            (volunteer_id, start_date, end_date)
        )
    else:
        return query_db(
            '''SELECT * FROM volunteer_schedules
               WHERE volunteer_id = %s
               ORDER BY schedule_date DESC, start_time''',
            (volunteer_id,)
        )

def create_distribution(client_id, volunteer_id, distribution_date, weight_kg, 
                       items_description, client_signature=False, notes=''):
    """Create a distribution record"""
    return query_db(
        '''INSERT INTO distributions (client_id, volunteer_id, distribution_date, weight_kg, 
                                     items_description, client_signature, notes)
           VALUES (%s, %s, %s, %s, %s, %s, %s)''',
        (client_id, volunteer_id, distribution_date, weight_kg, items_description, 
         client_signature, notes),
        commit=True
    )


