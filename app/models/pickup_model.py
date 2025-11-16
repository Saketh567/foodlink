"""
Pickup Model
User food pickup operations
"""
from app.database import query_db

def create_pickup(user_id, inventory_id, quantity, status='pending'):
    """Create a new pickup request"""
    return query_db(
        '''INSERT INTO pickups (user_id, inventory_id, quantity, status)
           VALUES (%s, %s, %s, %s)''',
        (user_id, inventory_id, quantity, status),
        commit=True
    )

def get_pickup_by_id(pickup_id):
    """Get pickup record by ID"""
    return query_db(
        '''SELECT p.*, u.full_name as user_name, f.food_category
           FROM pickups p
           JOIN users u ON p.user_id = u.user_id
           JOIN food_inventory f ON p.inventory_id = f.inventory_id
           WHERE p.pickup_id = %s''',
        (pickup_id,),
        one=True
    )

def get_pickups_by_user(user_id, limit=None):
    """Get all pickups for a specific user"""
    query = '''SELECT p.*, f.food_category
               FROM pickups p
               JOIN food_inventory f ON p.inventory_id = f.inventory_id
               WHERE p.user_id = %s
               ORDER BY p.created_at DESC'''
    if limit:
        query += f' LIMIT {limit}'
    return query_db(query, (user_id,))

def get_pending_pickups():
    """Get all pending pickup requests"""
    return query_db(
        '''SELECT p.*, u.full_name as user_name, f.food_category
           FROM pickups p
           JOIN users u ON p.user_id = u.user_id
           JOIN food_inventory f ON p.inventory_id = f.inventory_id
           WHERE p.status = "pending"
           ORDER BY p.created_at DESC'''
    )

def update_pickup_status(pickup_id, status):
    """Update pickup status (pending -> approved -> completed/rejected)"""
    return query_db(
        'UPDATE pickups SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE pickup_id = %s',
        (status, pickup_id),
        commit=True
    )

def get_pickup_statistics(start_date=None, end_date=None):
    """Get pickup statistics (total quantity by date)"""
    if start_date and end_date:
        return query_db(
            '''SELECT DATE(created_at) as date,
                      COUNT(*) as num_pickups,
                      SUM(quantity) as total_quantity
               FROM pickups
               WHERE DATE(created_at) BETWEEN %s AND %s
               GROUP BY DATE(created_at)
               ORDER BY date DESC''',
            (start_date, end_date)
        )
    else:
        return query_db(
            '''SELECT DATE(created_at) as date,
                      COUNT(*) as num_pickups,
                      SUM(quantity) as total_quantity
               FROM pickups
               GROUP BY DATE(created_at)
               ORDER BY date DESC
               LIMIT 30'''
        )
