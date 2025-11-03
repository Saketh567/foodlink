"""
Utility script to generate password hashes for the database
Usage: python generate_password_hash.py
"""
from app.utils.security import hash_password

if __name__ == '__main__':
    passwords = {
        'Admin@123': 'admin@foodlink.com',
        'Volunteer@123': 'volunteer@foodlink.com'
    }
    
    print("=" * 60)
    print("Password Hash Generator for FoodLink Connect")
    print("=" * 60)
    print()
    
    for password, email in passwords.items():
        hashed = hash_password(password)
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"Hash: {hashed}")
        print()
        print(f"SQL INSERT statement:")
        print(f"UPDATE users SET password_hash = '{hashed}' WHERE email = '{email}';")
        print("-" * 60)
        print()

