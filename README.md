# SmartOps — Production-Grade SaaS Backend

> Cloud-ready, multi-tenant Django REST Framework backend with event-driven architecture, real-time capabilities, and observability.

---

## 🏗 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Nginx (Reverse Proxy)                    │
│                    Static files · WebSocket · API               │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   Django + Gunicorn (WSGI/ASGI)                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │  Users   │ │   Orgs   │ │Workflows │ │  Billing         │   │
│  │  App     │ │   App    │ │  App     │ │  App             │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └───────┬──────────┘   │
│       │             │            │               │              │
│  ┌────▼─────────────▼────────────▼───────────────▼──────────┐   │
│  │              Core (Services · Events · Middleware)        │   │
│  │   TenantMiddleware · EventDispatcher · CacheService       │   │
│  │   AuditLog · RBAC Permissions · Rate Limiter              │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────┬───────────────────┬───────────────────┬────────────────┘
         │                   │                   │
    ┌────▼────┐        ┌─────▼─────┐       ┌────▼────┐
    │ PostgreSQL│      │   Redis    │       │  Celery  │
    │ (Data)   │       │(Cache/PubSub)│     │(Workers) │
    └──────────┘       └───────────┘       └──────────┘
```

### Key Design Decisions

| Decision | Why |
|---|---|
| **Row-level tenant isolation** | Simpler than schema-per-tenant, works with all ORMs, easier to scale horizontally |
| **Services layer** | Keeps views thin, makes logic testable and reusable across Celery tasks and management commands |
| **Event-driven architecture** | Decouples components, enables async processing, supports eventual consistency |
| **Dead letter handling** | Ensures no event is silently lost — failed events are stored for manual replay |
| **Thread-local tenant context** | Propagates tenant through the request lifecycle without passing it through every function |
| **UUID primary keys** | Globally unique, safe for distributed systems and cross-service references |
| **Split settings** | Environment-based configuration prevents secrets leaking and allows targeted optimizations |

---

## 📁 Project Structure

```
smartops/
├── apps/
│   ├── core/                    # Shared foundation
│   │   ├── models/              # Base models (TimeStamped, TenantAware)
│   │   ├── middleware/          # Tenant, RequestID, RateLimit
│   │   ├── events/             # Domain event system
│   │   ├── views/              # Health check
│   │   ├── permissions.py      # RBAC
│   │   ├── audit.py            # Audit logging
│   │   ├── cache.py            # Redis cache service
│   │   └── tasks.py            # Celery event processor
│   ├── users/                   # Authentication & profiles
│   ├── organizations/          # Multi-tenant management
│   ├── workflows/              # Workflow engine
│   ├── billing/                # Invoicing & subscriptions
│   └── notifications/          # In-app + WebSocket notifications
├── config/
│   ├── settings/               # Environment-based settings
│   │   ├── base.py             # Shared configuration
│   │   ├── development.py      # Local dev overrides
│   │   ├── staging.py          # QA environment
│   │   └── production.py       # Production hardening
│   ├── celery.py               # Celery app config
│   ├── asgi.py                 # ASGI with Channels
│   ├── urls.py                 # Root URL routing
│   └── wsgi.py                 # WSGI entrypoint
├── tests/                      # pytest-django test suite
├── nginx/                      # Nginx reverse proxy config
├── docker-compose.yml          # Development environment
├── docker-compose.prod.yml     # Production environment
├── Dockerfile                  # Multi-stage production build
├── gunicorn.conf.py            # WSGI server config
└── .github/workflows/ci.yml   # CI/CD pipeline
```

---

## 🚀 Quick Start

### 1. Clone & Configure
```bash
git clone https://github.com/your-org/smartops.git
cd smartops
cp .env.example .env    # Edit with your values
```

### 2. Development (Docker)
```bash
docker compose up --build
# API: http://localhost:8000
# Swagger: http://localhost:8000/swagger/
# PgAdmin: http://localhost:5050
# Flower: http://localhost:5555
```

### 3. Production
```bash
docker compose -f docker-compose.prod.yml up --build -d
# App: http://localhost (via nginx)
```

### 4. Run Tests
```bash
pytest tests/ -v
```

---

## 🔑 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/users/register/` | POST | Register user (optional org creation) |
| `/api/users/login/` | POST | Get JWT tokens |
| `/api/users/profile/` | GET | Current user profile |
| `/api/users/switch-tenant/` | POST | Switch active organization |
| `/api/organizations/` | CRUD | Organization management |
| `/api/organizations/{id}/members/` | GET | List members |
| `/api/organizations/{id}/invite/` | POST | Invite member |
| `/api/workflows/` | CRUD | Workflow definitions |
| `/api/workflows/{id}/execute/` | POST | Trigger execution |
| `/api/billing/invoices/` | CRUD | Invoice management |
| `/api/billing/invoices/{id}/pay/` | POST | Mark as paid |
| `/api/notifications/` | GET | List notifications |
| `/health/` | GET | System health check |
| `/swagger/` | GET | API documentation |
| `ws://host/ws/notifications/` | WS | Real-time notifications |

---

## 🏢 Multi-Tenancy

Every request is scoped to a tenant (organization):

1. **JWT Login** → User gets an access token
2. **TenantMiddleware** → Extracts tenant from user's active org or `X-Tenant-ID` header
3. **TenantManager** → Auto-filters all ORM queries by tenant
4. **TenantAwareModel** → Auto-populates `tenant_id` on save

Switch tenant context:
```bash
curl -X POST /api/users/switch-tenant/ \
  -H "Authorization: Bearer <token>" \
  -d '{"organization_id": "<uuid>"}'
```

---

## 📡 Event-Driven Architecture

```
Service → EventDispatcher → Celery Task → EventRegistry → Handlers
                                  ↓ (on failure)
                           Retry (exponential backoff)
                                  ↓ (max retries exceeded)
                           Dead Letter Storage
```

**Supported Events:** `user_created`, `invoice_paid`, `workflow_completed`, `role_changed`

---

## 📈 Scaling Strategy

| Component | Scaling Method |
|---|---|
| **Django API** | Horizontal: add more Gunicorn container replicas behind load balancer |
| **Celery Workers** | Horizontal: increase `--concurrency` or add worker containers |
| **PostgreSQL** | Vertical first, then read replicas for heavy read workloads |
| **Redis** | Redis Cluster for high-availability caching |
| **WebSocket** | Scale via Redis channel layer (shared pub/sub across instances) |

### Database Optimization
- Connection pooling via `CONN_MAX_AGE`
- Strategic indexes on frequently queried columns
- `select_related` / `prefetch_related` to prevent N+1 queries
- UUID PKs for distributed compatibility

---

## 🔒 Security

- **RBAC** with role hierarchy: OWNER > ADMIN > MEMBER > VIEWER
- **Audit logging** for login, data changes, and role changes
- **Rate limiting** via Redis sliding window algorithm
- **CORS** restrictions with configurable allowed origins
- **HSTS, CSP, XSS protection** headers in production
- **Non-root Docker user** to prevent container escape attacks
- **Strong password validation** (min 10 chars, complexity requirements)
- **JWT with token rotation** and blacklisting on refresh

---

## 🔍 Observability

- **Structured JSON logging** via `python-json-logger`
- **Request ID tracing** (auto-generated UUID per request)
- **Prometheus metrics** at `/metrics`
- **Sentry integration** with Django + Celery + Redis
- **Health endpoint** at `/health/` checking DB, Redis, and Celery

---

## 🛠 CI/CD

GitHub Actions pipeline:
1. **Test** — Runs pytest with PostgreSQL + Redis services
2. **Lint** — flake8, isort, black
3. **Build** — Docker image build with layer caching

---

## License

Proprietary. All rights reserved.
