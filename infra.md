# AIOps Guardian — Infrastructure Guide

Companion to `readme.md` (vision/features) and `plan.md` (build sequence). This file documents the local infrastructure stack, the project's file system layout, ports/configuration, and day-to-day usage commands. Everything here targets **local infrastructure only** (Docker, Minikube, host Windows) — no cloud services.

---

## 1. Infrastructure Stack

All services run locally via Docker Compose (plus Minikube for Kubernetes agents/tests). Nothing here requires a cloud account.

| Service | Purpose | Introduced in |
|---|---|---|
| **Postgres** | System of record — incidents, investigations, evidence, reports, users | Phase 1 |
| **Redis** | Job queue (Celery/arq) + cache — never source of truth | Phase 1 (idle until Phase 3 async) |
| **Ollama** | Local LLM runtime (Llama 3 / Qwen / Gemma) for summarization + root-cause reasoning | Phase 1 |
| **Sample target app** | A deliberately breakable app (its own small web service + DB dependency) used as the investigation target | Phase 1 |
| **Minikube** | Local Kubernetes cluster for the Kubernetes Agent | Phase 2 |
| **ChromaDB** | Vector store for the RAG Agent (runbooks, SOPs, past incidents) | Phase 4 |
| **Prometheus** | Metrics scraping (host + containers) | Phase 5 |
| **Grafana** | Dashboards over Prometheus/Loki — used to dogfood the platform's own health | Phase 5 |
| **Loki + Promtail** | Log aggregation, cross-checked against direct-collection agents | Phase 5 |
| **Node Exporter** | Host-level metrics for Prometheus | Phase 5 |

### Compose files

```
docker/
├── docker-compose.core.yml        # Postgres, Redis, Ollama — always running
├── docker-compose.target.yml      # breakable sample app used as investigation target
├── docker-compose.observability.yml   # Prometheus, Grafana, Loki, Promtail, Node Exporter
└── docker-compose.override.yml    # local-only overrides (gitignored)
```

Kubernetes manifests for the sample app (used with Minikube) live under `kubernetes/sample-app/`.

---

## 2. File System / Project Structure

```
AIOps-Guardian/
│
├── agents/
│   ├── coordinator/        # LangGraph graph definition + InvestigationState schema
│   ├── linux/
│   ├── windows/
│   ├── docker/
│   ├── kubernetes/
│   ├── deployment/         # GitHub Actions / CI evidence collection
│   ├── network/
│   ├── metrics/
│   ├── database/
│   ├── rag/                # ChromaDB-backed retrieval agent
│   └── rootcause/           # root-cause correlation + incident report generation
│
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entrypoint
│   │   ├── config.py        # pydantic-settings
│   │   ├── auth.py          # API-key + JWT middleware
│   │   ├── routers/         # /investigate, /investigations, /chat, /auth
│   │   └── llm_client.py    # shared Ollama/LangChain wrapper
│   └── workers/             # Celery/arq worker entrypoint (Phase 3+)
│
├── frontend/                 # Next.js + React + TailwindCSS dashboard
│
├── rag/
│   └── knowledge_base/       # runbooks, SOPs, troubleshooting docs (markdown, embedded into ChromaDB)
│
├── monitoring/
│   ├── prometheus/
│   ├── grafana/
│   └── loki/
│
├── docker/                   # compose files (see above)
├── kubernetes/
│   └── sample-app/           # breakable Deployment/Service manifests for Minikube
│
├── database/
│   ├── models.py             # SQLAlchemy models
│   └── migrations/           # Alembic
│
├── reports/                  # generated incident reports (markdown/JSON), gitignored except samples
├── docs/                      # architecture.md, contributor guide, sequence diagrams
├── tests/
│   ├── unit/                 # per-agent tests, mocked SDK clients
│   └── integration/          # real-infra tests (break a container/pod, assert correct report)
│
├── .env.example
├── readme.md
├── plan.md
└── infra.md
```

---

## 3. Environment & Configuration

Configuration is centralized via `pydantic-settings`, loaded from `.env` (never committed — see `.env.example`).

Key variables:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Postgres connection string |
| `REDIS_URL` | Redis connection string |
| `OLLAMA_BASE_URL` | Ollama server address (default `http://localhost:11434`) |
| `OLLAMA_MODEL` | Model name (e.g. `qwen2.5:7b`, `llama3:8b`) |
| `CHROMA_PERSIST_DIR` | Local path for ChromaDB persistence |
| `API_KEY` | Shared secret for service-to-service `/investigate` calls |
| `JWT_SECRET` | Dashboard user auth (Phase 6) |
| `GITHUB_TOKEN` | Read-only PAT for Deployment Agent's GitHub Actions lookups |
| `KUBECONFIG` | Path to Minikube kubeconfig used by the Kubernetes Agent |
| `LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING` |

---

## 4. Ports

| Port | Service |
|---|---|
| 8000 | FastAPI backend |
| 3000 | Next.js frontend |
| 5432 | Postgres |
| 6379 | Redis |
| 11434 | Ollama |
| 8001 | ChromaDB |
| 9090 | Prometheus |
| 3001 | Grafana (offset from frontend's 3000) |
| 3100 | Loki |
| 9100 | Node Exporter |
| 8080 / target-app ports | Sample breakable app (defined in `docker-compose.target.yml`) |

Minikube's own service ports are assigned dynamically — use `minikube service list` to inspect.

---

## 5. Usage

### First-time setup

```bash
# core services (Postgres, Redis, Ollama)
docker compose -f docker/docker-compose.core.yml up -d

# pull the local LLM
docker exec -it ollama ollama pull qwen2.5:7b

# run DB migrations
alembic upgrade head

# start the breakable sample target app
docker compose -f docker/docker-compose.target.yml up -d

# backend (dev)
uvicorn backend.app.main:app --reload

# frontend (dev, once scaffolded in Phase 4)
cd frontend && npm run dev
```

### Kubernetes agent testing (Phase 2+)

```bash
minikube start
kubectl apply -f kubernetes/sample-app/
kubectl set image deployment/sample-app sample-app=broken-image:latest   # induce a failure
```

### Triggering an investigation

```bash
curl -X POST http://localhost:8000/investigate \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"target": "sample-app", "description": "site returning 502"}'
```

Async mode (Phase 3+) returns `{"investigation_id": "..."}` immediately — poll:

```bash
curl http://localhost:8000/investigations/<id> -H "X-API-Key: $API_KEY"
```

### Observability stack (Phase 5+)

```bash
docker compose -f docker/docker-compose.observability.yml up -d
# Grafana: http://localhost:3001 (default admin/admin, change on first login)
# Prometheus: http://localhost:9090
```

### Running tests

```bash
pytest tests/unit           # fast, mocked SDK clients
pytest tests/integration    # requires core + target stack running
```

---

## 6. Data Persistence

- **Postgres** — named Docker volume (`pg_data`), the only system of record. Back this up before any destructive `docker compose down -v`.
- **ChromaDB** — persisted to `CHROMA_PERSIST_DIR` (bind-mounted, not a named volume, so runbooks are easy to inspect/edit directly).
- **Grafana** — named volume (`grafana_data`) for dashboard definitions.
- **Reports** — written to `reports/` on disk in addition to being stored in Postgres, so they can be reviewed without hitting the API.

`docker compose down` (no `-v`) is safe for routine restarts; `-v` destroys the above volumes and should only be used intentionally.
