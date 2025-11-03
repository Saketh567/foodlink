"""
Database Connection Manager
Handles MySQL connections using connection pooling for better performance
"""
import mysql.connector
from mysql.connector import pooling
from flask import g, current_app

# Global connection pool
connection_pool = None

def init_db(app):
    """Initialize database connection pool"""
    global connection_pool
    
    try:
        connection_pool = pooling.MySQLConnectionPool(
            pool_name="foodlink_pool",
            pool_size=5,
            pool_reset_session=True,
            host=app.config['MYSQL_HOST'],
            port=app.config['MYSQL_PORT'],
            database=app.config['MYSQL_DATABASE'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            autocommit=False
        )
        print("✓ Database connection pool initialized successfully")
    except mysql.connector.Error as err:
        print(f"✗ Error initializing database: {err}")
        raise

def get_db():
    """Get database connection from pool"""
    if 'db' not in g:
        g.db = connection_pool.get_connection()
    return g.db

def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False, commit=False):
    """
    Execute a database query
    
    Args:
        query: SQL query string
        args: Query parameters (tuple)
        one: Return single row or all rows
        commit: Whether to commit transaction
    
    Returns:
        Query results or None
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute(query, args)
        
        if commit:
            db.commit()
            return cursor.lastrowid
        
        rv = cursor.fetchall()
        cursor.close()
        return (rv[0] if rv else None) if one else rv
    
    except mysql.connector.Error as err:
        db.rollback()
        print(f"Database error: {err}")
        raise
    finally:
        cursor.close()


