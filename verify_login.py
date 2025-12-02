import requests
from app.utils.security import hash_password
from app.utils.helpers import query_db
from app import create_app

app = create_app()

def verify_user_and_login():
    with app.app_context():
        # 1. Verify User in DB
        print("--- Verifying User in DB ---")
        user = query_db("SELECT user_id, email, role, is_active, password_hash FROM users WHERE email='volunteer@test.com'", one=True)
        if user:
            print(f"User found: ID={user['user_id']}, Email={user['email']}, Role={user['role']}, Active={user['is_active']}")
            # Verify password manually to be sure
            from werkzeug.security import check_password_hash
            is_valid = check_password_hash(user['password_hash'], 'password123')
            print(f"Password 'password123' valid? {is_valid}")
        else:
            print("User 'volunteer@test.com' NOT found in DB.")
            return

    # 2. Test Login via Requests
    print("\n--- Testing Login via Requests ---")
    session = requests.Session()
    login_url = "http://127.0.0.1:5000/auth/login"
    
    # Get CSRF token if needed (Flask-WTF not used here apparently, but good to check page load)
    response = session.get(login_url)
    print(f"GET Login Page: {response.status_code}")
    
    # Post credentials
    data = {
        "email": "volunteer@test.com",
        "password": "password123",
        "requested_role": "volunteer"
    }
    
    response = session.post(login_url, data=data, allow_redirects=False)
    print(f"POST Login: {response.status_code}")
    print(f"Redirect Location: {response.headers.get('Location')}")
    print(f"Cookies: {session.cookies.get_dict()}")
    
    if response.status_code == 302:
        redirect_url = response.headers.get('Location')
        if "/volunteer/dashboard" in redirect_url:
            print("SUCCESS: Redirected to volunteer dashboard.")
            
            # Follow redirect
            dashboard_response = session.get("http://127.0.0.1:5000" + redirect_url)
            print(f"GET Dashboard: {dashboard_response.status_code}")
            if "Welcome" in dashboard_response.text or "Dashboard" in dashboard_response.text:
                 print("Dashboard loaded successfully.")
            else:
                 print("Dashboard loaded but content might be missing.")
        else:
            print(f"FAILURE: Redirected to {redirect_url} instead of dashboard.")
    else:
        print("FAILURE: Login did not redirect.")

if __name__ == "__main__":
    verify_user_and_login()
