from app.utils.security import hash_password
from app.utils.helpers import execute_db
from app import create_app

app = create_app()

def update_pass():
    with app.app_context():
        new_hash = hash_password("password123")
        print(f"Generated hash: {new_hash}")
        execute_db("UPDATE users SET password_hash=%s WHERE email='volunteer@test.com'", (new_hash,))
        print("Updated volunteer password.")

if __name__ == "__main__":
    update_pass()
