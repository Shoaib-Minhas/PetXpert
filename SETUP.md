# PetXpert - Setup Guide

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd PetXpert_Final_Updated
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# For development (includes debugging tools)
pip install -r requirements/development.txt

# For production
pip install -r requirements/production.txt

# Quick installation (base only)
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development, PostgreSQL for production)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key
STRIPE_SECRET_KEY=sk_test_your_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Email Configuration (optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### 5. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000`

## Project Structure

```
PetXpert_Final_Updated/
├── apps/                    # Django applications
│   ├── accounts/           # User authentication
│   ├── appointments/       # Appointment booking
│   ├── payments/          # Stripe payment integration
│   ├── pets/              # Pet management
│   ├── veterinarians/     # Veterinarian profiles
│   └── ...
├── config/                # Django configuration
│   ├── settings/         # Environment-specific settings
│   ├── urls.py           # URL routing
│   └── wsgi.py           # WSGI configuration
├── templates/             # HTML templates
├── static/               # Static files (CSS, JS)
├── media/                # User uploaded files
├── requirements/         # Python dependencies
│   ├── base.txt          # Core dependencies
│   ├── development.txt   # Development tools
│   └── production.txt    # Production dependencies
├── manage.py             # Django management script
└── requirements.txt      # Quick installation file
```

## Key Features

- **User Authentication**: JWT-based authentication system
- **Veterinarian Profiles**: Search and book appointments with veterinarians
- **Pet Management**: Add and manage pet profiles
- **Appointment Booking**: Real-time scheduling with 1-hour slots
- **Stripe Payment Integration**: Secure hosted checkout
- **Review System**: Rate and review veterinarians
- **Responsive Design**: Mobile-friendly interface

## API Endpoints

### Authentication
- `POST /api/signup/` - User registration
- `POST /api/signin/` - User login
- `POST /api/token/refresh/` - Refresh JWT token

### Appointments
- `GET /api/appointments/available-slots/` - Get available time slots
- `POST /api/appointments/` - Create appointment

### Payments
- `POST /api/payments/create-checkout-session/` - Create Stripe checkout
- `POST /api/webhooks/stripe/` - Stripe webhook handler

## Stripe Configuration

### Test Mode (Development)
1. Go to [Stripe Dashboard](https://dashboard.stripe.com/test/apikeys)
2. Copy your test API keys
3. Add them to your `.env` file

### Production
1. Go to [Stripe Dashboard](https://dashboard.stripe.com/apikeys)
2. Copy your live API keys
3. Set up webhook endpoints in Stripe dashboard
4. Add webhook secret to `.env` file

### Webhook Events
- `checkout.session.completed` - Payment successful, create appointment

## Troubleshooting

### ModuleNotFoundError: No module named 'stripe'
```bash
pip install stripe
```

### Database migration errors
```bash
python manage.py migrate --run-syncdb
```

### Static files not loading
```bash
python manage.py collectstatic
```

## Production Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn config.wsgi:application
```

### Using Whitenoise (for static files)

Add to `settings/production.py`:
```python
MIDDLEWARE.insert(0, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

### Environment Variables

Set `DEBUG=False` and configure production database in `.env` file.

## Support

For issues and questions, please refer to the project documentation or contact the development team.
