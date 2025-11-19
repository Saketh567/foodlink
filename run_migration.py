"""
Migration Runner Script
Runs the add_client_photo migration to add photo_path column to clients table
"""
import mysql.connector
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def run_migration():
    """Run the migration to add photo_path column"""
    try:
        # Get database configuration
        host = os.environ.get('MYSQL_HOST') or 'localhost'
        port = int(os.environ.get('MYSQL_PORT') or 3306)
        user = os.environ.get('MYSQL_USER') or 'foodlink_user'
        password = os.environ.get('MYSQL_PASSWORD') or 'your_password'
        database = os.environ.get('MYSQL_DATABASE') or 'foodlink_db'
        
        print("Connecting to database...")
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        cursor = connection.cursor()
        
        # Check if column already exists
        print("Checking if photo_path column already exists...")
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'clients' 
            AND COLUMN_NAME = 'photo_path'
        """, (database,))
        
        result = cursor.fetchone()
        if result[0] > 0:
            print("✓ photo_path column already exists. Migration not needed.")
            cursor.close()
            connection.close()
            return
        
        # Run migration
        print("Running migration: Adding photo_path column to clients table...")
        
        # Add photo_path column
        cursor.execute("""
            ALTER TABLE clients 
            ADD COLUMN photo_path VARCHAR(500) NULL AFTER income_proof_path
        """)
        
        # Add index
        print("Adding index on photo_path...")
        try:
            cursor.execute("""
                CREATE INDEX idx_photo_path ON clients(photo_path)
            """)
        except mysql.connector.Error as e:
            # Index might already exist, that's okay
            if "Duplicate key name" not in str(e):
                raise
        
        # Commit changes
        connection.commit()
        
        print("✓ Migration completed successfully!")
        print("  - Added photo_path column to clients table")
        print("  - Added index on photo_path column")
        
        cursor.close()
        connection.close()
        
    except mysql.connector.Error as err:
        print(f"✗ Database error: {err}")
        if connection:
            connection.rollback()
        raise
    except Exception as e:
        print(f"✗ Error running migration: {e}")
        raise

if __name__ == '__main__':
    print("=" * 50)
    print("FoodLink Connect - Migration Runner")
    print("Migration: Add photo_path to clients table")
    print("=" * 50)
    print()
    
    run_migration()
    
    print()
    print("=" * 50)
    print("Migration process completed!")
    print("=" * 50)

