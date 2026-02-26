"""
Development Settings — Local development overrides.
Usage: DJANGO_SETTINGS_MODULE=config.settings.development
"""
from config.settings.base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ['*']

# Use verbose logging in development
LOGGING['handlers']['console']['formatter'] = 'verbose'  # noqa: F405
LOGGING['root']['level'] = 'DEBUG'  # noqa: F405

# Disable rate limiting in development
RATE_LIMIT_REQUESTS = 10000

# Allow all CORS in development
CORS_ALLOW_ALL_ORIGINS = True

# Browsable API in development
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (  # noqa: F405
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
)
