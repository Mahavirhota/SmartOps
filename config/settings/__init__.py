"""
Settings package — Environment-based configuration split.

Architecture Decision:
Splitting settings by environment prevents production secrets from
leaking into development and allows environment-specific optimizations.

Usage:
    DJANGO_SETTINGS_MODULE=config.settings.development  # local dev
    DJANGO_SETTINGS_MODULE=config.settings.production    # production
"""
# Default to development settings for local use
from config.settings.base import *  # noqa: F401,F403
