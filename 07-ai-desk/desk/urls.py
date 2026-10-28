from django.urls import path,re_path
from . import views as v
from django.urls import register_converter
urlpatterns=[path('api/v1/readiness',v.readiness),path('api/v1/openapi.json',v.schema),path('api/v1/health',v.health),path('api/v1/session',v.session),path('api/v1/login',v.signin),path('api/v1/logout',v.signout),path('api/v1/chats',v.chats),path('api/v1/chats/<int:pk>',v.chat),path('api/v1/chats/<int:pk>/ask',v.ask),path('api/v1/documents',v.documents),path('api/v1/sources/<int:pk>',v.source),re_path(r'^(?P<path>.*)$',v.frontend)]


