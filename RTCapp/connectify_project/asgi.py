import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE","connectify_project.settings")
from django.core.asgi import get_asgi_application
django_asgi_app=get_asgi_application()
from django.conf import settings
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from meetings.routing import websocket_urlpatterns
http_app=ASGIStaticFilesHandler(django_asgi_app) if settings.DEBUG else django_asgi_app
application=ProtocolTypeRouter({"http":http_app,"websocket":AuthMiddlewareStack(URLRouter(websocket_urlpatterns))})
