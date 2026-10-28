from pathlib import Path
import secrets,os
BASE_DIR=Path(__file__).resolve().parent.parent
secret=BASE_DIR/'.local-secret'
if not secret.exists(): secret.write_text(secrets.token_urlsafe(48))
SECRET_KEY=secret.read_text().strip()
DEBUG=False
ALLOWED_HOSTS=['127.0.0.1','localhost','testserver']
INSTALLED_APPS=['django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','rest_framework','desk']
MIDDLEWARE=['desk.middleware.RequestLog','django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware']
ROOT_URLCONF='desk.urls'
DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':os.environ.get('AIDESK_DATABASE',str(BASE_DIR/'data.sqlite3'))}}
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
USE_TZ=True
SESSION_COOKIE_NAME='aidesk_session'
CSRF_COOKIE_NAME='aidesk_csrf'
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE='Strict'
CSRF_COOKIE_SAMESITE='Strict'
SESSION_COOKIE_AGE=28800
SECURE_CONTENT_TYPE_NOSNIFF=True
DATA_UPLOAD_MAX_MEMORY_SIZE=5*1024*1024
FILE_UPLOAD_MAX_MEMORY_SIZE=5*1024*1024
REST_FRAMEWORK={'DEFAULT_AUTHENTICATION_CLASSES':['rest_framework.authentication.SessionAuthentication'],'DEFAULT_PERMISSION_CLASSES':['rest_framework.permissions.IsAuthenticated'],'DEFAULT_THROTTLE_CLASSES':['rest_framework.throttling.UserRateThrottle'],'DEFAULT_THROTTLE_RATES':{'user':'120/min'}}
OLLAMA_URL='http://127.0.0.1:11434'
OLLAMA_MODEL='qwen3.5:4b'
