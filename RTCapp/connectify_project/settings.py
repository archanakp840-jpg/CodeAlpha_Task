import os,json
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured
BASE_DIR=Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR/".env")
SECRET_KEY=os.getenv("DJANGO_SECRET_KEY","dev-only-change-me-before-deployment")
DEBUG=os.getenv("DJANGO_DEBUG","True").lower()=="true"
if not DEBUG and (len(SECRET_KEY)<50 or any(marker in SECRET_KEY.lower() for marker in ("dev-only", "replace-this", "change-me"))):
    raise ImproperlyConfigured("Set DJANGO_SECRET_KEY to a private random value of at least 50 characters when DEBUG=False.")
ALLOWED_HOSTS=[h for h in os.getenv("DJANGO_ALLOWED_HOSTS","localhost,127.0.0.1").split(",") if h]
INSTALLED_APPS=["django.contrib.admin","django.contrib.auth","django.contrib.contenttypes","django.contrib.sessions","django.contrib.messages","django.contrib.staticfiles","rest_framework","channels","meetings"]
MIDDLEWARE=["django.middleware.security.SecurityMiddleware","django.contrib.sessions.middleware.SessionMiddleware","django.middleware.common.CommonMiddleware","django.middleware.csrf.CsrfViewMiddleware","django.contrib.auth.middleware.AuthenticationMiddleware","django.contrib.messages.middleware.MessageMiddleware","django.middleware.clickjacking.XFrameOptionsMiddleware"]
ROOT_URLCONF="connectify_project.urls"
TEMPLATES=[{"BACKEND":"django.template.backends.django.DjangoTemplates","DIRS":[BASE_DIR/"templates"],"APP_DIRS":True,"OPTIONS":{"context_processors":["django.template.context_processors.request","django.contrib.auth.context_processors.auth","django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION="connectify_project.wsgi.application"
ASGI_APPLICATION="connectify_project.asgi.application"
DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":BASE_DIR/"db.sqlite3"}}
AUTH_PASSWORD_VALIDATORS=[{"NAME":"django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},{"NAME":"django.contrib.auth.password_validation.MinimumLengthValidator"},{"NAME":"django.contrib.auth.password_validation.CommonPasswordValidator"},{"NAME":"django.contrib.auth.password_validation.NumericPasswordValidator"}]
LANGUAGE_CODE="en-us"
TIME_ZONE="Asia/Kolkata"
USE_I18N=True
USE_TZ=True
STATIC_URL="/static/"
STATICFILES_DIRS=[BASE_DIR/"static"]
STATIC_ROOT=BASE_DIR/"staticfiles"
MEDIA_ROOT=BASE_DIR/"private_uploads"
DEFAULT_AUTO_FIELD="django.db.models.BigAutoField"
LOGIN_URL="/login/"
LOGIN_REDIRECT_URL="/dashboard/"
LOGOUT_REDIRECT_URL="/login/"
CHANNEL_LAYERS={"default":{"BACKEND":"channels.layers.InMemoryChannelLayer"}}
MAX_UPLOAD_BYTES=int(os.getenv("MAX_UPLOAD_MB","20"))*1024*1024
try:
    RTC_ICE_SERVERS=json.loads(os.getenv("RTC_ICE_SERVERS", '[{"urls":"stun:stun.l.google.com:19302"}]'))
except json.JSONDecodeError as exc:
    raise ImproperlyConfigured("RTC_ICE_SERVERS must be a JSON array.") from exc
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS="DENY"
CSRF_COOKIE_HTTPONLY=True
SESSION_COOKIE_HTTPONLY=True
SECURE_REFERRER_POLICY="same-origin"
SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO","https")
if not DEBUG:
    SECURE_SSL_REDIRECT=True
    SESSION_COOKIE_SECURE=True
    CSRF_COOKIE_SECURE=True
