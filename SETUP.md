# PetXpert - Setup Guide

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Installation Steps


cd PetXpert
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
# Install all dependencies (recommended)
pip install -r requirements/development.txt

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

# Groq API (required for AI Diagnosis)
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

> **Important**: Get your Groq API key at [https://console.groq.com/keys](https://console.groq.com/keys). The AI Diagnosis feature will not work without it.

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
PetXpert/
├── apps/                    # Django applications
│   ├── accounts/           # User authentication
│   ├── appointments/       # Appointment booking
│   ├── chat/               # AI Diagnosis chat system
│   ├── diagnosis/          # Diagnosis records
│   ├── payments/           # Stripe payment integration
│   ├── pets/               # Pet management
│   └── veterinarians/      # Veterinarian profiles
├── config/                 # Django configuration
│   ├── settings/           # Environment-specific settings
│   ├── urls.py             # URL routing
│   └── wsgi.py             # WSGI configuration
├── services/               # AI Diagnosis service layer
│   ├── chat_service.py     # Chat orchestration
│   ├── llm_service.py      # Groq API integration (Llama 3.3 70B)
│   ├── image_service.py    # Image classification (ViT)
│   ├── rag_service.py      # Retrieval-Augmented Generation
│   ├── disease_mapping.py  # Veterinary knowledge base
│   └── ml/                 # Machine learning models
│       └── efficientnet_model.py  # EfficientNet B3/B4 classifier
├── templates/              # HTML templates
│   ├── layouts/            # Base layout with sidebar
│   ├── diagnosis/          # AI Diagnosis page
│   └── ...
├── static/                 # Static files (CSS, JS)
│   ├── css/
│   │   └── ai-diagnosis.css
│   └── js/
│       └── ai-diagnosis.js
├── uploads/                # Uploaded pet images (AI Diagnosis)
├── media/                  # User uploaded files (avatars, pets)
├── requirements/           # Python dependencies
│   ├── ai.txt              # AI/ML dependencies
│   ├── base.txt            # Core dependencies
│   ├── development.txt     # Development tools
│   └── production.txt      # Production dependencies
├── manage.py               # Django management script
├── requirements.txt        # Quick installation file
└── .gitignore              # Git ignore rules
```

## Key Features

- **AI Diagnosis**: AI-powered pet health assessment with symptom analysis, image upload (EfficientNet B3/B4 classification), and real-time SSE streaming responses via Groq API (Llama 3.3 70B)
- **User Authentication**: JWT-based authentication system
- **Veterinarian Profiles**: Search and book appointments with veterinarians
- **Pet Management**: Add and manage pet profiles with medical history
- **Appointment Booking**: Real-time scheduling with 1-hour slots
- **Stripe Payment Integration**: Secure hosted checkout
- **Review System**: Rate and review veterinarians
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS
- **Secure by Default**: `.env` excluded from git, push protection enabled

## AI Diagnosis Feature

The AI Diagnosis page (`/ai-diagnosis/`) provides an AI-powered veterinary assistant that:

- Accepts text descriptions of pet symptoms
- Supports image upload for visual analysis
- Streams AI responses in real-time via Server-Sent Events (SSE)
- Uses EfficientNet B3/B4 for image classification and Groq's Llama 3.3 70B for text generation
- Includes a veterinary knowledge base covering 5 disease categories
- Generates structured diagnoses with treatment plans and vet urgency guidance
- Supports RAG (Retrieval-Augmented Generation) for context-aware responses

### Enabling AI Diagnosis

1. Get a Groq API key from [https://console.groq.com/keys](https://console.groq.com/keys)
2. Add it to your `.env` file as `GROQ_API_KEY`
3. Install the `groq` package:
   ```bash
   pip install groq
   ```
4. Restart the development server

### Optional: Image Classification Model (EfficientNet)

For pet disease image classification, a fine-tuned EfficientNet B3/B4 model is used:

```bash
pip install torch torchvision Pillow
```

Place the model checkpoint at `data/model_checkpoints/efficientnet-pet-disease.pth`.
The feature degrades gracefully if the model is not available (falls back to text-only diagnosis).

### Optional: RAG with ONNX Embeddings

For higher-quality semantic search in the RAG system:

```bash
pip install optimum[onnxruntime] transformers
```

Falls back to TF-IDF embeddings if ONNX is not available.

## API Endpoints

### Authentication
- `POST /api/signup/` - User registration
- `POST /api/signin/` - User login
- `POST /api/token/refresh/` - Refresh JWT token
- `GET /api/profile/` - Get user profile
- `PUT /api/profile/` - Update user profile

### Appointments
- `GET /api/appointments/available-slots/` - Get available time slots
- `POST /api/appointments/` - Create appointment

### Payments
- `POST /api/payments/create-checkout-session/` - Create Stripe checkout
- `POST /api/webhooks/stripe/` - Stripe webhook handler

### AI Diagnosis (Chat)
- `POST /api/v1/chat/sessions` - Create a new chat session
- `GET /api/v1/chat/sessions/<id>` - Get session details
- `DELETE /api/v1/chat/sessions/<id>` - Delete a session
- `GET /api/v1/chat/sessions/<id>/messages` - Get session messages
- `POST /api/v1/chat/sessions/<id>/messages/send` - Send message (non-streaming)
- `POST /api/v1/chat/sessions/<id>/messages/stream` - Send message (SSE streaming)
- `GET /api/v1/chat/sessions/<id>/diagnosis` - Get latest diagnosis
- `GET /api/v1/health` - Health check

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

### ModuleNotFoundError: No module named 'groq'
```bash
pip install groq
```

### AI Diagnosis not responding
- Ensure `GROQ_API_KEY` is set in `.env`
- Verify the API key at [https://console.groq.com/keys](https://console.groq.com/keys)
- Check your Groq account has available credits

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

Required for production:
```
DEBUG=False
SECRET_KEY=<strong-random-key>
DATABASE_URL=postgresql://...
GROQ_API_KEY=gsk_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## Support

For issues and questions, please refer to the project documentation or open an issue on GitHub.


Set `DEBUG=False` and configure production database in `.env` file.

## Support

For issues and questions, please refer to the project documentation or contact the development team.
