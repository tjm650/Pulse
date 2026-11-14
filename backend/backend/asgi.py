"""ASGI entry point for Django HTTP handling; realtime is provided by Supabase."""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

from django.core.asgi import get_asgi_application

application = get_asgi_application()
