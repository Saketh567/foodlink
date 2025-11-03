# FoodLink Connect

A comprehensive food rescue and distribution management system connecting food donors with families in need.

## 🎯 Overview

FoodLink Connect is a Flask-based web application designed to streamline the process of food donation collection, verification, and distribution. It provides separate portals for administrators, volunteers, and clients to manage the entire food rescue workflow.

## 📋 Features

### For Administrators
- Dashboard with comprehensive statistics
- Client verification and management
- User management across all roles
- Detailed reports and analytics
- Donation tracking and monitoring

### For Volunteers
- Log food pickups from donors
- Sign in clients for food distribution
- Track personal volunteer statistics
- View pickup history

### For Clients
- Registration and profile management
- View distribution history
- Update personal information
- Track received food assistance

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- MySQL 5.7+ or MariaDB 10.2+
- pip (Python package manager)

### Quick Installation Steps

1. **Navigate to project directory**
   ```bash
   cd FoodLink
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up MySQL database**
   ```bash
   # Login to MySQL
   mysql -u root -p
   
   # Run the schema file
   source migrations/schema.sql;
   EXIT;
   ```

5. **Configure environment variables**
   ```bash
   # Copy the example file
   copy .env.example .env   # Windows
   cp .env.example .env      # macOS/Linux
   
   # Edit .env with your MySQL credentials
   # Generate a secret key:
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

7. **Access the application**
   - Open your browser and navigate to: `http://localhost:5000`

### 📖 Detailed Setup Guide

For comprehensive step-by-step instructions with troubleshooting, see **[SETUP_GUIDE.md](SETUP_GUIDE.md)**

## 🔐 Default Login Credentials

**Admin:**
- Email: `admin@foodlink.com`
- Password: `Admin@123`

**Volunteer:**
- Email: `volunteer@foodlink.com`
- Password: `Volunteer@123`

⚠️ **IMPORTANT:** Change these passwords immediately in production!

## 📋 Features

### ✨ QR Code Functionality
- **Client QR Codes:** Each verified client gets a unique QR code
- **QR Code Scanning:** Volunteers can scan QR codes for quick client sign-in
- **Download QR Codes:** Clients can download their QR code as PNG image
- **Camera Integration:** Built-in HTML5 camera scanner for mobile devices

### 🎯 Role-Based Features

**Admin:**
- Dashboard with statistics
- Client verification and management
- User management
- Detailed reports and analytics
- Donation tracking

**Volunteer:**
- Log food pickups
- Scan QR codes or manually enter client numbers
- Sign in clients for distribution
- Track volunteer statistics
- View pickup history

**Client:**
- Registration with verification workflow
- View and download QR code
- Update profile information
- View distribution history

## 📁 Project Structure

```
FoodLink/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration settings
│   ├── database.py          # MySQL connection handler
│   ├── models/              # Data access layer
│   ├── routes/              # Route blueprints
│   ├── utils/              # Helper functions
│   ├── static/              # Static files (CSS, JS, images)
│   └── templates/          # HTML templates
├── migrations/
│   └── schema.sql          # Database schema
├── tests/                  # Unit tests
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
├── run.py                 # Application entry point
└── README.md             # This file
```

## 🛠️ Configuration

### Database Configuration

Edit the `.env` file with your MySQL credentials:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=foodlink_user
MYSQL_PASSWORD=your_secure_password
MYSQL_DATABASE=foodlink_db
```

### Application Settings

Key configuration options in `app/config.py`:
- `PICKUP_START_TIME`: Start time for food pickup window (default: 13:00)
- `PICKUP_END_TIME`: End time for food pickup window (default: 13:45)
- `CLIENT_NUMBER_PREFIX`: Prefix for client numbers (default: FL)
- `UPLOAD_FOLDER`: Directory for file uploads
- `MAX_CONTENT_LENGTH`: Maximum file upload size (default: 16MB)

## 📊 Database Schema

The application uses the following main tables:
- `users`: All system users (admin, volunteer, client)
- `clients`: Extended client information
- `donations`: Food pickup/donation records
- `distributions`: Food distribution to clients
- `volunteer_schedules`: Volunteer shift management
- `activity_logs`: Audit trail
- `food_inventory`: Current food stock

See `migrations/schema.sql` for complete schema definition.

## 🔒 Security Features

- Password hashing using SHA-256 (upgrade to bcrypt recommended for production)
- Role-based access control (RBAC)
- SQL injection prevention via parameterized queries
- Session management with secure cookies
- Input validation on all forms

## 🧪 Testing

```bash
# Run tests (when implemented)
pytest tests/
```

## 📝 Development

### Adding New Features

1. **Models**: Add data access functions in `app/models/`
2. **Routes**: Create route handlers in `app/routes/`
3. **Templates**: Add HTML templates in `app/templates/`
4. **Static Files**: Add CSS/JS in `app/static/`

### Code Style

- Follow PEP 8 Python style guide
- Use meaningful variable names
- Add docstrings to functions and classes
- Keep functions focused and single-purpose

## 🚢 Deployment

### Production Checklist

- [ ] Change all default passwords
- [ ] Generate secure `SECRET_KEY`
- [ ] Set `SESSION_COOKIE_SECURE = True` (requires HTTPS)
- [ ] Configure production database
- [ ] Set up proper logging
- [ ] Use WSGI server (Gunicorn)
- [ ] Configure reverse proxy (Nginx)
- [ ] Enable HTTPS/SSL
- [ ] Set up regular backups
- [ ] Configure firewall rules

### Using Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

For issues and questions:
- Check the documentation
- Review the code comments
- Open an issue on GitHub

## 🎯 Roadmap

- [ ] Email notifications
- [ ] Mobile app API
- [ ] Real-time updates (WebSocket)
- [ ] PDF report generation
- [ ] CSV export functionality
- [ ] Advanced analytics dashboard
- [ ] Multi-location support
- [ ] SMS notifications

---

**Built with ❤️ for fighting hunger and building stronger communities**


