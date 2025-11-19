"""
Verify Migration Script
Checks that the photo_path column was added successfully
"""
import mysql.connector
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def verify_migration():
    """Verify the migration was successful"""
    try:
        # Get database configuration
        host = os.environ.get('MYSQL_HOST') or 'localhost'
        port = int(os.environ.get('MYSQL_PORT') or 3306)
        user = os.environ.get('MYSQL_USER') or 'foodlink_user'
        password = os.environ.get('MYSQL_PASSWORD') or 'your_password'
        database = os.environ.get('MYSQL_DATABASE') or 'foodlink_db'
        
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        cursor = connection.cursor(dictionary=True)
        
        # Check column details
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE, COLUMN_DEFAULT
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'clients' 
            AND COLUMN_NAME = 'photo_path'
        """, (database,))
        
        result = cursor.fetchone()
        
        if result:
            print("✓ Migration verified successfully!")
            print(f"  Column: {result['COLUMN_NAME']}")
            print(f"  Type: {result['DATA_TYPE']}({result['CHARACTER_MAXIMUM_LENGTH']})")
            print(f"  Nullable: {result['IS_NULLABLE']}")
            print(f"  Default: {result['COLUMN_DEFAULT']}")
            
            # Check index
            cursor.execute("""
                SELECT INDEX_NAME, COLUMN_NAME
                FROM information_schema.STATISTICS
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = 'clients'
                AND COLUMN_NAME = 'photo_path'
            """, (database,))
            
            index_result = cursor.fetchone()
            if index_result:
                print(f"  Index: {index_result['INDEX_NAME']} on {index_result['COLUMN_NAME']}")
            else:
                print("  ⚠ Warning: Index not found (may not be critical)")
        else:
            print("✗ Migration verification failed: photo_path column not found")
            return False
        
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"✗ Error verifying migration: {e}")
        return False

if __name__ == '__main__':
    print("Verifying migration...")
    print()
    verify_migration()

