"""
Health Check Endpoint — Production readiness probe.

Architecture Decision:
Kubernetes and load balancers rely on health endpoints to determine
if a service instance is ready to receive traffic. This endpoint
checks all critical dependencies (DB, Redis, Celery) and returns
a structured response. A single unhealthy dependency makes the
entire service "unhealthy".
"""
import logging
from django.http import JsonResponse
from django.db import connection
from django.views import View
from django.conf import settings

logger = logging.getLogger(__name__)


class HealthCheckView(View):
    """
    Comprehensive health endpoint checking all critical dependencies.
    
    Returns:
        200: All systems healthy
        503: One or more systems unhealthy
        
    Response format:
    {
        "status": "healthy" | "unhealthy",
        "checks": {
            "database": {"status": "healthy", "latency_ms": 2.1},
            "redis": {"status": "healthy", "latency_ms": 0.5},
            "celery": {"status": "healthy", "workers": 2}
        }
    }
    """

    def get(self, request):
        checks = {}
        overall_healthy = True

        # 1. Database check
        checks['database'] = self._check_database()
        if checks['database']['status'] != 'healthy':
            overall_healthy = False

        # 2. Redis check
        checks['redis'] = self._check_redis()
        if checks['redis']['status'] != 'healthy':
            overall_healthy = False

        # 3. Celery check
        checks['celery'] = self._check_celery()
        if checks['celery']['status'] != 'healthy':
            overall_healthy = False

        response_data = {
            'status': 'healthy' if overall_healthy else 'unhealthy',
            'checks': checks,
        }

        status_code = 200 if overall_healthy else 503
        return JsonResponse(response_data, status=status_code)

    def _check_database(self) -> dict:
        """Check database connectivity and measure latency."""
        import time
        try:
            start = time.monotonic()
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            latency = (time.monotonic() - start) * 1000
            return {'status': 'healthy', 'latency_ms': round(latency, 2)}
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {'status': 'unhealthy', 'error': str(e)}

    def _check_redis(self) -> dict:
        """Check Redis connectivity and measure latency."""
        import time
        try:
            import redis
            r = redis.from_url(
                getattr(settings, 'CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
            )
            start = time.monotonic()
            r.ping()
            latency = (time.monotonic() - start) * 1000
            return {'status': 'healthy', 'latency_ms': round(latency, 2)}
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {'status': 'unhealthy', 'error': str(e)}

    def _check_celery(self) -> dict:
        """Check Celery worker availability."""
        try:
            from config.celery import app as celery_app
            inspect = celery_app.control.inspect(timeout=3.0)
            active_workers = inspect.active_queues()
            if active_workers:
                return {
                    'status': 'healthy',
                    'workers': len(active_workers),
                }
            return {'status': 'degraded', 'workers': 0, 'message': 'No active workers'}
        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            return {'status': 'unhealthy', 'error': str(e)}
