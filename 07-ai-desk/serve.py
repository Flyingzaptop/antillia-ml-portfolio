import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','desk.settings')
from django.core.wsgi import get_wsgi_application
from waitress import serve
serve(get_wsgi_application(),host='127.0.0.1',port=int(os.environ.get('PORT','8107')),threads=8,max_request_body_size=6*1024*1024)
