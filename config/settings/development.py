from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-development-key-for-petxpert')

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    
    # Internal Apps
    'apps.core',
    'apps.accounts',
    'apps.pets',
    'apps.diagnosis',
    'apps.chat',
    'apps.appointments',
    'apps.prescriptions',
    'apps.payments',
    'rest_framework',
    'rest_framework_simplejwt',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}

AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Stripe Configuration
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='sk_test_placeholder')
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='pk_test_placeholder')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='whsec_placeholder')

# ── AI Diagnosis / Chat Settings ──────────────────────────────────────────

# Groq API (Llama 3.3 70B for text generation)
GROQ_API_KEY = config('GROQ_API_KEY', default='')
GROQ_MODEL = config('GROQ_MODEL', default='llama-3.3-70b-versatile')

# EfficientNet Model (pet disease image classification)
# Options: 'efficientnet-b3' or 'efficientnet-b4'
EFFICIENTNET_VARIANT = config('EFFICIENTNET_VARIANT', default='efficientnet-b4')
EFFICIENTNET_NUM_CLASSES = int(config('EFFICIENTNET_NUM_CLASSES', default='5'))
EFFICIENTNET_MODEL_PATH = config(
    'EFFICIENTNET_MODEL_PATH',
    default=str(BASE_DIR / 'data' / 'model_checkpoints' / 'efficientnet-pet-disease.pth')
)
EFFICIENTNET_IMAGE_SIZE = int(config('EFFICIENTNET_IMAGE_SIZE', default='380'))
DEVICE = config('DEVICE', default='cpu')

# LLM Settings
LLM_TEMPERATURE = float(config('LLM_TEMPERATURE', default='0.4'))
LLM_MAX_TOKENS = int(config('LLM_MAX_TOKENS', default='1024'))

# File Upload
MAX_IMAGE_SIZE_MB = int(config('MAX_IMAGE_SIZE_MB', default='10'))
UPLOAD_DIR = BASE_DIR / 'uploads'

