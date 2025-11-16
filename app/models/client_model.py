"""
Client Model
Client-specific operations
"""
from app.database import query_db

def get_client_by_id(client_id):
    """Get client by ID with user information"""
    return query_db(
        '''SELECT c.*, u.email, u.full_name, u.phone, u.is_active, u.created_at
           FROM clients c
           JOIN users u ON c.user_id = u.user_id
           WHERE c.client_id = %s''',
        (client_id,),
        one=True
    )

def get_client_by_user_id(user_id):
    """Get client by user ID"""
    return query_db(
        '''SELECT c.*, u.email, u.full_name, u.phone
           FROM clients c
           JOIN users u ON c.user_id = u.user_id
           WHERE c.user_id = %s''',
        (user_id,),
        one=True
    )

def create_client(user_id, address, family_size, allergies='', food_preferences='', verification_status='pending'):
    """Create a new client"""
    return query_db(
        '''INSERT INTO clients (user_id, address, family_size, allergies, food_preferences, verification_status)
           VALUES (%s, %s, %s, %s, %s, %s)''',
        (user_id, address, family_size, allergies, food_preferences, verification_status),
        commit=True
    )

def update_client(client_id, **kwargs):
    """Update client information"""
    updates = []
    values = []
    
    allowed_fields = ['address', 'family_size', 'allergies', 'food_preferences', 
                      'verification_status', 'client_number', 'verified_date', 'verified_by', 'notes']
    for field, value in kwargs.items():
        if field in allowed_fields:
            updates.append(f"{field} = %s")
            values.append(value)
    
    if not updates:
        return None
    
    values.append(client_id)
    query = f"UPDATE clients SET {', '.join(updates)} WHERE client_id = %s"
    return query_db(query, tuple(values), commit=True)

def get_pending_clients():
    """Get all clients pending verification"""
    return query_db(
        '''SELECT c.*, u.full_name, u.email, u.phone, u.created_at
           FROM clients c
           JOIN users u ON c.user_id = u.user_id
           WHERE c.verification_status = "pending"
           ORDER BY u.created_at DESC'''
    )

def get_verified_clients():
    """Get all verified clients"""
    return query_db(
        '''SELECT c.*, u.full_name, u.email, u.phone
           FROM clients c
           JOIN users u ON c.user_id = u.user_id
           WHERE c.verification_status = "verified"
           ORDER BY c.verified_date DESC'''
    )

def get_client_distributions(client_id):
    """Get all distributions for a client"""
    return query_db(
        '''SELECT d.*, u.full_name as volunteer_name
           FROM distributions d
           JOIN users u ON d.volunteer_id = u.user_id
           WHERE d.client_id = %s
           ORDER BY d.distribution_date DESC''',
        (client_id,)
    )


