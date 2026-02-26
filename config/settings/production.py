"""
Production Settings — Hardened for production deployment.
Usage: DJANGO_SETTINGS_MODULE=config.settings.production
"""
from config.settings.base import *  # noqa: F401,F403

DEBUG = False

# ── Security Hardening ────────────────────────────────────────────
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ── Performance ───────────────────────────────────────────────────
# DB connection pooling: keep connections alive for 10 mins
DATABASES['default']['CONN_MAX_AGE'] = 600  # noqa: F405

# Use JSON-only rendering in production (no browsable API)
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (  # noqa: F405
    'rest_framework.renderers.JSONRenderer',
)

# ── Sentry with lower trace sampling for cost control ─────────────
SENTRY_TRACES_SAMPLE_RATE = 0.1
