from app import create_app
from app.database import get_db

def fix_schema():
    app = create_app()
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("SHOW COLUMNS FROM clients")
        columns = [row[0] for row in cursor.fetchall()] # row is tuple in raw connector or dict? 
        # app.database.query_db uses dictionary=True, but here I'm using raw cursor.
        # Let's use the app's query_db to be safe or just use raw sql.
        
        # Actually, let's just use execute_db from app.database if possible, or just raw cursor.
        # The app.database module has query_db.
        
        print(f"Existing columns: {columns}")
        
        alter_queries = []
        if 'address_original' not in columns:
            alter_queries.append("ADD COLUMN address_original TEXT AFTER address")
        if 'address_standardized' not in columns:
            alter_queries.append("ADD COLUMN address_standardized TEXT AFTER address_original")
        if 'address_validation_source' not in columns:
            alter_queries.append("ADD COLUMN address_validation_source VARCHAR(50) AFTER address_standardized")
        if 'address_validated_at' not in columns:
            alter_queries.append("ADD COLUMN address_validated_at DATETIME NULL AFTER address_validation_source")
        if 'no_show_count' not in columns:
            alter_queries.append("ADD COLUMN no_show_count INT NOT NULL DEFAULT 0 AFTER notes")
            
        for q in alter_queries:
            full_query = f"ALTER TABLE clients {q}"
            print(f"Executing: {full_query}")
            cursor.execute(full_query)
            
        conn.commit()
        print("Schema update complete.")

if __name__ == "__main__":
    fix_schema()
