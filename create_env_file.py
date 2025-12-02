"""
Script to create .env file for FoodLink Connect.
Run this script to generate your .env file with MySQL settings.
"""
import os
import secrets


def create_env_file():
    """Create .env file with template values."""
    secret_key = secrets.token_hex(32)

    print("=" * 60)
    print("FoodLink Connect - Environment File Setup")
    print("=" * 60)
    print()
    print("This script will create a .env file with your configuration.")
    print()

    mysql_user = input("MySQL Username (default: root): ").strip() or "root"
    mysql_password = input("MySQL Password: ").strip()

    if not mysql_password:
        print("\nWARNING: No password entered. Using default 'your_password'")
        print("         Please edit .env file manually after creation.")
        mysql_password = "your_password"

    env_content = f"""# Application Configuration
SECRET_KEY={secret_key}
FLASK_ENV=development

# MySQL Database
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER={mysql_user}
MYSQL_PASSWORD={mysql_password}
MYSQL_DATABASE=foodlink_db

# Application Port
PORT=5000
"""

    env_path = ".env"
    with open(env_path, "w", encoding="utf-8") as env_file:
        env_file.write(env_content)

    print()
    print(".env file created successfully!")
    print(f"Location: {os.path.abspath(env_path)}")
    print()
    print("Next steps:")
    print("  1. Verify the .env file has correct MySQL password")
    print("  2. Run: python run.py")
    print()


if __name__ == "__main__":
    create_env_file()
