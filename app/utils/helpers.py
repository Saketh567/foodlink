"""
General Utility Functions
Helper functions for common operations
"""
from datetime import datetime, date
from flask import current_app

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def format_date(date_obj, format_string='%Y-%m-%d'):
    """Format date object to string"""
    if date_obj is None:
        return ''
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime(format_string)

def format_datetime(datetime_obj, format_string='%Y-%m-%d %H:%M:%S'):
    """Format datetime object to string"""
    if datetime_obj is None:
        return ''
    if isinstance(datetime_obj, str):
        return datetime_obj
    return datetime_obj.strftime(format_string)

def is_within_pickup_window():
    """Check if current time is within food pickup window"""
    now = datetime.now().time()
    start = datetime.strptime(current_app.config['PICKUP_START_TIME'], '%H:%M').time()
    end = datetime.strptime(current_app.config['PICKUP_END_TIME'], '%H:%M').time()
    return start <= now <= end


