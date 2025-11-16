"""
User Model
User CRUD operations
"""
from app.database import query_db

def get_user_by_id(user_id):
    """Get user by ID"""
    return query_db(
        'SELECT * FROM users WHERE user_id = %s',
        (user_id,),
        one=True
    )

def get_user_by_email(email):
    """Get user by email"""
    return query_db(
        'SELECT * FROM users WHERE email = %s',
        (email,),
        one=True
    )

def create_user(email, password_hash, full_name, phone, role, is_active=False):
    """Create a new user"""
    return query_db(
        '''INSERT INTO users (email, password_hash, full_name, phone, role, is_active)
           VALUES (%s, %s, %s, %s, %s, %s)''',
        (email, password_hash, full_name, phone, role, is_active),
        commit=True
    )

def update_user(user_id, **kwargs):
    """Update user information"""
    updates = []
    values = []
    
    allowed_fields = ['email', 'full_name', 'phone', 'is_active']
    for field, value in kwargs.items():
        if field in allowed_fields:
            updates.append(f"{field} = %s")
            values.append(value)
    
    if not updates:
        return None
    
    values.append(user_id)
    query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s"
    return query_db(query, tuple(values), commit=True)

def get_all_users(role=None):
    """Get all users, optionally filtered by role"""
    if role:
        return query_db(
            'SELECT * FROM users WHERE role = %s ORDER BY created_at DESC',
            (role,)
        )
    return query_db('SELECT * FROM users ORDER BY created_at DESC')


