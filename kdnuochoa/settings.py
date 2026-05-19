"""
Django settings for kdnuochoa project.
"""

from pathlib import Path
import os
import django.template.loaders.filesystem as fs

BASE_DIR = Path(__file__).resolve().parent.parent


print("TEMPLATE DIRS:", BASE_DIR / 'templates')


SECRET_KEY = 'django-insecure-5@ut1(^#=_=z%mmrbg%lkc&wr#@e&xp5qgpv^*6&0btenn7ux0'

DEBUG = True

ALLOWED_HOSTS = ['*']


# ═══════════════════════════════════════════════════════
# INSTALLED_APPS
# QUAN TRỌNG: Xóa 'jazzmin' — nó override toàn bộ template
# admin của chúng ta. Thay bằng 'django.contrib.admin' thuần.
# ═══════════════════════════════════════════════════════
INSTALLED_APPS = [
    # ❌ BỎ 'jazzmin' — đang conflict với luxury theme
    # 'jazzmin',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app',
    'nested_admin',
    'ckeditor',
    'ckeditor_uploader',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'kdnuochoa.urls'

# ═══════════════════════════════════════════════════════
# TEMPLATES
# APP_DIRS = False để tránh Django tự tìm template trong app
# Dùng loaders thủ công để ưu tiên thư mục templates/ của project
# ═══════════════════════════════════════════════════════
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',   # ← luxury theme ở đây (ưu tiên cao nhất)
        ],
        # APP_DIRS: True = Django tìm templates trong mỗi app
        # Để True vì nested_admin và ckeditor cần tìm template của chúng
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'app.context_processors.global_data',
            ],
        },
    },
]

WSGI_APPLICATION = 'kdnuochoa.wsgi.application'

# ═══════════════════════════════════════════════════════
# DATABASE — SQL Server
# ═══════════════════════════════════════════════════════
DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'QL_KDNuocHoa',
        'USER': 'doan2',
        'PASSWORD': '1111',
        'HOST': 'localhost',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
            'unicode_results': True,
            'extra_params':    'charset=utf8',
        },
    }
}

# ═══════════════════════════════════════════════════════
# STATIC & MEDIA
# ═══════════════════════════════════════════════════════
STATIC_URL = '/static/'
# Thêm vào — nơi collectstatic gom file
STATIC_ROOT = BASE_DIR / 'staticfiles'
_extra_static = BASE_DIR / 'app' / 'static'
STATICFILES_DIRS = []
if _extra_static.exists():
    STATICFILES_DIRS.append(_extra_static)

STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

CKEDITOR_UPLOAD_PATH = "uploads/"

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]

CKEDITOR_CONFIGS = {
    'default': {
        'filebrowserUploadUrl': '/ckeditor/upload/',
        'filebrowserBrowseUrl': '/ckeditor/browse/',
    }
}

# ═══════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ═══════════════════════════════════════════════════════
# INTERNATIONALISATION
# ═══════════════════════════════════════════════════════
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ═══════════════════════════════════════════════════════
# PAYMENT GATEWAYS
# ═══════════════════════════════════════════════════════
VNPAY_TMN_CODE    = "BRH4CBDX"
VNPAY_HASH_SECRET = "5R0WH1ZTB8I4SHUKCI1BHKLNTC6AAASA"
VNPAY_URL         = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
VNPAY_RETURN_URL  = "http://localhost:8000/thanh-toan/vnpay-return/"

MOMO_PARTNER_CODE = "MOMO"
MOMO_ACCESS_KEY   = "F8BBA842ECF85"
MOMO_SECRET_KEY   = "K951B6PE1waDMi640xX08PD3vg6EkVlz"
MOMO_ENDPOINT     = "https://test-payment.momo.vn/v2/gateway/api/create"
MOMO_RETURN_URL   = "http://localhost:8000/thanh-toan/momo-return/"
MOMO_NOTIFY_URL   = "http://localhost:8000/api/momo-ipn/"


# Cấu hình email — dùng Gmail SMTP
# ═══════════════════════════════════════════════════════════════
 
EMAIL_BACKEND      = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST         = 'smtp.gmail.com'
EMAIL_PORT         = 587
EMAIL_USE_TLS      = True
EMAIL_HOST_USER    = 'lhngocc1304@gmail.com'      # ← đổi thành email của bạn
EMAIL_HOST_PASSWORD = 'drtp jeuw vnim ztqb'         # ← App Password (không phải mk thường)
DEFAULT_FROM_EMAIL = 'Ami Perfumery <your_gmail@gmail.com>'


# ═══════════════════════════════════════════════════════
# AI — OpenAI GPT-4o
# ═══════════════════════════════════════════════════════
import os
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")