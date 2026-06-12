"""
Django settings for kdnuochoa project.
"""

from pathlib import Path
import os
import django.template.loaders.filesystem as fs
from dotenv import load_dotenv 



BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')  


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
    'social_django',
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
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
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
ADMIN_NOTIFY_EMAIL = "lhngocc1304@gmail.com"
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


# facebook/google
# AUTHENTICATION_BACKENDS = (
#     'social_core.backends.facebook.FacebookOAuth2',
#     'social_core.backends.google.GoogleOAuth2',
#     'django.contrib.auth.backends.ModelBackend',
# )
SOCIAL_AUTH_BACKEND_CLASSES = [
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
]
SOCIAL_AUTH_ENABLED_BACKENDS = (
    'social_core.backends.facebook.FacebookOAuth2',
    'social_core.backends.google.GoogleOAuth2',
)

# Google OAuth credentials
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY    = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.environ.get('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE  = ['email', 'profile']

# Facebook OAuth credentials
SOCIAL_AUTH_FACEBOOK_KEY    = os.environ.get('SOCIAL_AUTH_FACEBOOK_KEY', '')
SOCIAL_AUTH_FACEBOOK_SECRET = os.environ.get('SOCIAL_AUTH_FACEBOOK_SECRET', '')
SOCIAL_AUTH_FACEBOOK_SCOPE  = ['email', 'public_profile']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {'fields': 'id,name,email,picture'}

# Pipeline
# SOCIAL_AUTH_PIPELINE = (
#     'social_core.pipeline.social_auth.social_details',
#     'social_core.pipeline.social_auth.social_uid',
#     'social_core.pipeline.social_auth.auth_allowed',
#     'social_core.pipeline.social_auth.social_user',
#     'social_core.pipeline.user.get_username',
#     'social_core.pipeline.user.create_user',
#     'social_core.pipeline.social_auth.associate_user',
#     'social_core.pipeline.social_auth.load_extra_data',
#     'social_core.pipeline.user.user_details',
#     'app.pipeline.save_ami_session',         # pipeline tùy chỉnh
# )

LOGIN_REDIRECT_URL  = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL           = '/auth/'
# SOCIAL_AUTH_URL_NAMESPACE = 'social'
# Sau khi social login xong → redirect về đây
# SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/'
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/'


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
DEFAULT_FROM_EMAIL = 'Ami Perfumery <lhngocc1304@gmail.com>'


# ═══════════════════════════════════════════════════════
# AI — OpenAI GPT-4o
# ═══════════════════════════════════════════════════════
import os
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")