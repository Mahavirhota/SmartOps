"""
Gunicorn Configuration — Production-grade WSGI server settings.

Architecture Decision:
- Workers: 2 × CPU cores + 1 (recommended for I/O-bound Django apps)
- Graceful timeout: allows in-flight requests to complete on restart
- Access log: structured for log aggregation (ELK, CloudWatch, etc.)
- Pre-fork model: each worker is an isolated process for stability
"""
import multiprocessing

# ── Server Socket ─────────────────────────────────────────────────

bind = '0.0.0.0:8000'
backlog = 2048

# ── Worker Processes ──────────────────────────────────────────────
# Formula: 2 x CPU + 1 (handles I/O-bound workloads efficiently)

workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'gthread'
threads = 2
worker_connections = 1000
max_requests = 1000           # Restart workers after N requests (prevents memory leaks)
max_requests_jitter = 50      # Random jitter to prevent all workers restarting at once

# ── Timeouts ──────────────────────────────────────────────────────

timeout = 30                  # Kill worker if request takes > 30s
graceful_timeout = 30         # Time for in-flight requests to finish on restart
keepalive = 5                 # Keep TCP connections alive for 5s

# ── Logging ───────────────────────────────────────────────────────

accesslog = '-'               # Log to stdout (for container log aggregation)
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# ── Process Naming ────────────────────────────────────────────────

proc_name = 'smartops'

# ── Server Hooks ──────────────────────────────────────────────────

def on_starting(server):
    """Log when gunicorn is starting."""
    pass


def post_fork(server, worker):
    """Called after a worker is forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")


def pre_exec(server):
    """Called before master process is re-spawned."""
    server.log.info("Forked child, re-executing.")
