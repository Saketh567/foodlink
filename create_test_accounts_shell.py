"""
Flask shell script to create test accounts
Run with: flask shell < create_test_accounts_shell.py
"""
from app.utils.security import hash_password
from app.utils.helpers import execute_db, query_db

# Create volunteer account
volunteer_email = "volunteer@test.com"
volunteer_password = "password123"
volunteer_name = "Test Volunteer"

# Create client account  
client_email = "client@test.com"
client_password = "password123"
client_name = "Test Client"

print("Creating test accounts...")

# Check if volunteer exists
existing_volunteer = query_db("SELECT user_id FROM users WHERE email=%s", (volunteer_email,), one=True)
if not existing_volunteer:
    execute_db(
        "INSERT INTO users (email, password_hash, full_name, role, is_active) VALUES (%s, %s, %s, 'volunteer', 1)",
        (volunteer_email, hash_password(volunteer_password), volunteer_name)
    )
    print(f"✓ Created volunteer: {volunteer_email} / {volunteer_password}")
else:
    print(f"✓ Volunteer already exists: {volunteer_email}")

# Check if client exists
existing_client = query_db("SELECT user_id FROM users WHERE email=%s", (client_email,), one=True)
if not existing_client:
    # Create user
    execute_db(
        "INSERT INTO users (email, password_hash, full_name, role, is_active) VALUES (%s, %s, %s, 'client', 1)",
        (client_email, hash_password(client_password), client_name)
    )
    
    # Get user_id
    client_user = query_db("SELECT user_id FROM users WHERE email=%s", (client_email,), one=True)
    user_id = client_user["user_id"]
    
    # Create client profile
    execute_db(
        """INSERT INTO clients (user_id, address, family_size, verification_status, client_number, verified_date)
        VALUES (%s, %s, %s, 'verified', %s, NOW())""",
        (user_id, "123 Test St, Vancouver, BC", 3, f"CL{user_id:05d}")
    )
    print(f"✓ Created verified client: {client_email} / {client_password}")
else:
    print(f"✓ Client already exists: {client_email}")
    # Make sure client is verified
    client_user = query_db("SELECT user_id FROM users WHERE email=%s", (client_email,), one=True)
    execute_db(
        "UPDATE clients SET verification_status='verified', client_number=%s WHERE user_id=%s",
        (f"CL{client_user['user_id']:05d}", client_user["user_id"])
    )
    print("  ✓ Ensured client is verified")

print("\n=== Test Accounts ===")
print(f"Volunteer: {volunteer_email} / {volunteer_password}")
print(f"Client: {client_email} / {client_password}")
print("=====================")
