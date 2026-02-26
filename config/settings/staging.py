"""
Staging Settings — Near-production for QA testing.
Usage: DJANGO_SETTINGS_MODULE=config.settings.staging
"""
from config.settings.base import *  # noqa: F401,F403

DEBUG = False

# Staging is accessible but not public-facing
SECURE_SSL_REDIRECT = False  # SSL handled by load balancer in staging

# Use full Sentry traces for debugging staging issues
SENTRY_TRACES_SAMPLE_RATE = 0.5
