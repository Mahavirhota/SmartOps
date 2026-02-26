from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Core application configuration."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core'

    def ready(self) -> None:
        """Import signal handlers and event registry on app startup."""
        import apps.core.signals  # noqa: F401
