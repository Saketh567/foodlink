"""
FoodLink Connect - Main Application Entry Point
Run this file to start the Flask development server
"""
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from app import create_app

app = create_app()

if __name__ == '__main__':
    # Get port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Run in debug mode for development
    app.run(host='0.0.0.0', port=port, debug=True)


