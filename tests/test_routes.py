"""
Unit Tests for Routes
Run with: pytest tests/test_routes.py
"""
import pytest
from app import create_app

@pytest.fixture
def app():
    """Create application instance for testing"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['MYSQL_DATABASE'] = 'foodlink_test_db'
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

def test_index_page(client):
    """Test index page loads"""
    response = client.get('/')
    assert response.status_code == 200

def test_login_page(client):
    """Test login page loads"""
    response = client.get('/auth/login')
    assert response.status_code == 200

def test_register_page(client):
    """Test register page loads"""
    response = client.get('/auth/register')
    assert response.status_code == 200

# Add more tests as needed

