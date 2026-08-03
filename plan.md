# AIOps Guardian — Build Plan

## Context

`readme.md` describes the vision for AIOps Guardian: a multi-agent AI platform that automatically investigates production incidents (crashed containers, failed deployments, resource exhaustion, etc.) and produces a root-cause report with a confidence score and remediation recommendation. As of now the repo contains only that README — no code, no structure.

This plan turns that vision into a buildable sequence, scoped for a **4-6 week, ~4-6 hrs/day** effort, targeting a genuinely working (not mocked) **production-grade platform** — real agents, real local infrastructure (Docker/Minikube/host Windows), real persistence, real auth, real error handling. Phase 1 deliberately starts with the backend + a single working agent end-to-end, before touching the frontend or the full observability stack, so there's always something runnable to build on.

---

## Guardrails — what "production-grade" means at this scope

**In scope:**
- Typed config (`pydantic-settings`), structured JSON logging with a correlation ID threaded through every agent call
- One failing agent (timeout, SSH drop, Docker API error) never crashes the whole investigation — it degrades to partial evidence with a `failed`/`degraded` flag
- Per-agent timeouts + retries (lightweight, not a service mesh)
- Real auth boundary: API key for service-to-service triggers, JWT for the dashboard — not SSO/OIDC
- Schema-validated agent outputs (Pydantic everywhere an LLM or SDK returns data) — the Root Cause Agent never parses free text
- A pipeline that runs against real local infra you can intentionally break (Docker, Minikube, real Postgres, real Windows event log)
- Automated tests: unit tests per agent (mocked SDK clients) + at least one real integration test against live broken infra

**Explicitly not in scope (over-engineering at this timeline):**
- Multi-tenant SaaS auth, SSO/OIDC
- High availability, clustering, multi-region
- Full observability SLOs / distributed tracing (OpenTelemetry spans are a stretch goal, not a requirement)
- Horizontal agent scaling / message-bus architecture beyond a single Redis-backed queue
- Any cloud provider integration — this build is 100% local/on-prem

---

## Phase 1 — Days 1-5: Backend skeleton + Coordinator + Docker Agent (end-to-end)

**Goal:** one real agent, working against a real broken Docker container, returning a real report.

- **Day 1:** Repo scaffold matching README structure (`agents/`, `backend/`, `docker/`, `database/`, `tests/`, `docs/`). Python env. FastAPI skeleton with `/health`. `pydantic-settings` config. Structured JSON logging. `docker-compose.yml` with Postgres + Redis + Ollama; pull a small local model (Qwen2.5 or Llama3 8B).
- **Day 2:** Postgres schema (Alembic) for `incidents`, `investigations`, `evidence`, `reports`. SQLAlchemy models. Stand up a "sample target app" docker-compose stack you can deliberately break.
- **Day 3:** Define `InvestigationState` and `EvidenceItem` Pydantic schemas. First LangGraph graph: `Coordinator → DockerAgent → END`. Docker Agent via `docker-py`: container status, logs tail, restart count, health state.
- **Day 4:** Wire graph into `POST /investigate` (sync), persist investigation + evidence to Postgres. Ollama-backed summarization inside the Docker Agent. API-key auth middleware. Global FastAPI exception handlers.
- **Day 5:** Break the sample app (stop a container / bad env var crash loop), call `/investigate`, verify correct evidence + summary. First pytest tests (mocked Docker client + one real integration test).

**Key architectural decisions:**
- `InvestigationState`: incident metadata + `List[EvidenceItem]` + per-agent status dict + root-cause result + report — the contract every future agent honors.
- `EvidenceItem` schema: `{agent, source_type, severity, summary, raw_data(ref), confidence_signal, timestamp}` — uniform enough that the Root Cause Agent never special-cases an agent.
- Sync execution for now — deferred to async in Phase 3 once parallel agents make it worth the complexity.
- Ollama invoked via a shared `llm_client` wrapper (LangChain `ChatOllama`), never called ad hoc per agent.
- API-key header auth as baseline (no dashboard yet, so no JWT/users needed).

**Verify:** stop/break a container in the sample stack → `POST /investigate` → response correctly identifies the down container → row present in `investigations`/`evidence` tables.

---

## Phase 2 — Days 6-10: Kubernetes Agent + Deployment Agent + Root Cause Agent v1

**Goal:** replicate the README's own flagship example (CrashLoopBackOff + failed deploy + DB creds → root cause) end-to-end.

- **Day 6:** Minikube setup; deploy the sample app to k8s (breakable via bad image tag / bad env var / OOMKill). Kubernetes Python client wired up.
- **Day 7:** Kubernetes Agent: pod status, CrashLoopBackOff/OOMKilled detection, rollout status, recent events — normalized into the same `EvidenceItem` schema as Docker.
- **Day 8:** Extend the graph to fan out in parallel (Coordinator → [Docker, Kubernetes] → join node). Deployment Agent: GitHub Actions API client pulling recent workflow runs/commit SHAs, flagging "deploy occurred near incident time."
- **Day 9:** Root Cause Agent v1 — Ollama-backed correlation prompt over the full evidence list, Pydantic output parser (`root_cause`, `confidence 0-100`, `contributing_evidence[]`, `reasoning`).
- **Day 10:** Incident Report Agent v1 (assemble evidence + root cause + timeline into a stored markdown/JSON report). End-to-end test replicating the README's "Website Down" scenario.

**Key architectural decisions:**
- Parallel fan-out pattern for independent collection agents (LangGraph parallel branches / `asyncio.gather` inside a node) — the pattern every later agent (Metrics, DB, Linux, Network, Windows) slots into.
- Root Cause Agent consumes *only* the normalized evidence list — never raw Docker/K8s SDK objects — proving the Phase 1 schema decision holds under a second, differently-shaped agent.

**Verify:** deploy a bad image + wrong DB credential env var to the Minikube app; `/investigate` should produce a root cause resembling the README's own example, with a plausible confidence score.

---

## Phase 3 — Days 11-15: Database + Metrics Agents, async job queue, reliability basics

**Goal:** complete the README's "Collect Infra Data → Logs → Metrics → Deployment History" workflow, and make the system resilient now that 4+ agents run per investigation.

- **Day 11:** Database Agent — Postgres connectivity, connection count, `pg_stat_activity`-based slow query/connection-exhaustion check.
- **Day 12:** Metrics Agent — host CPU/mem/disk via `psutil` + per-container resource usage via Docker stats.
- **Day 13:** Move `/investigate` to async: Redis + Celery/arq job queue. Endpoint returns `investigation_id` immediately (202); `GET /investigations/{id}` for polling. Per-agent timeout + retry decorator (agent fails/times out → `degraded`, investigation continues with partial evidence).
- **Day 14:** Correlation-ID threading through coordinator → worker → every agent's logs. Error taxonomy (`AgentTimeoutError`, `AgentConnectionError`, ...) with tests simulating a hung agent.
- **Day 15:** Verify: kill the DB container *and* spike CPU concurrently mid-investigation; confirm all agents report correctly in parallel and Root Cause Agent still produces one coherent conclusion from 5+ evidence sources.

**Key architectural decisions:**
- Sync→async transition deliberately happens here, not Phase 1 — only once there's a real multi-agent latency problem, avoiding premature complexity.
- Redis is a queue/cache, never the system of record — Postgres remains the only source of truth.
- "Degraded but complete" (partial evidence + explicit failure flag) becomes the standard resilience pattern going forward.

**Verify:** inject a hung agent (sleep) and confirm the investigation completes within its timeout budget with `degraded: true` rather than hanging.

---

## Phase 4 — Days 16-20: RAG knowledge base + Linux Agent + Network Agent + Frontend kickoff

**Goal:** add the RAG advisor now that there's real incident history to seed it with, and start the dashboard now that the API contract is stable.

- **Day 16:** ChromaDB stood up; seed with 5-8 runbooks/SOP markdown docs + backfilled embeddings of incidents already closed in Phases 1-3.
- **Day 17:** RAG Agent — retrieves top-k similar runbooks/past incidents given current evidence, feeds them into the Root Cause Agent's prompt as supporting context (not a competing decision-maker). Wired as a node feeding Root Cause, not parallel with collection agents.
- **Day 18:** Linux Agent — targets a Linux container/WSL2 (`docker exec` or `paramiko` SSH), parses `journalctl`/`syslog`/`auth.log` for errors in the incident window.
- **Day 19:** Network Agent — connectivity checks (socket connect, DNS resolution, port reachability). **Frontend kickoff:** Next.js + Tailwind scaffold, typed API client generated from the backend's OpenAPI schema, incident list page against `GET /investigations`.
- **Day 20:** Frontend investigation-detail page (per-agent evidence, timeline, root cause + confidence, recommendation). Verify RAG surfaces a seeded runbook on a repeat-pattern incident, and Linux/Network agents produce correct evidence for a syslog error / blocked port scenario.

**Why here, not earlier:** RAG needs real incident history to be more than an empty vector store — seeding it in Phase 1-2 would just be fixture data pretending to be knowledge. The frontend starts once the API surface (multiple endpoints, evidence sub-resources, report shape) has stabilized under async + 6 agents; starting earlier would mean rebuilding the UI's data layer repeatedly.

**Verify:** trigger an incident matching a seeded runbook's pattern; confirm the report links back to that runbook and the reasoning reflects it.

---

## Phase 5 — Days 21-25: Windows Event Viewer Agent + Observability stack + Frontend continued

**Goal:** add native Windows investigation (the dev machine is Windows); stand up Prometheus/Grafana/Loki as a second, cross-checking data path — not a replacement for the direct-collection agents.

- **Day 21:** Windows Agent — `pywin32`/`win32evtlog` (or `Get-WinEvent` via subprocess) reading Application/System event logs for the incident window, plus key `Get-Service` checks. Security log parsing kept light — deep audit correlation deferred.
- **Day 22:** Node Exporter + Prometheus + Grafana + Loki/promtail docker-compose services, scraping host + containers.
- **Day 23:** Grafana dashboards for the platform's own health (investigation latency, per-agent success/failure rates) — dogfooding observability on AIOps Guardian itself. Optional Metrics Agent v2 path querying Prometheus via PromQL alongside `psutil`.
- **Day 24-25:** Frontend: live in-flight investigation status (polling), historical incident list/filter, a lightweight NL query box hitting a single-turn `/chat` endpoint (maps text like "why is my API down" to triggering/looking up an investigation — no conversational memory).

**Why observability comes after the agents:** Prometheus/Grafana/Loki are valuable once there's something real to observe and a second evidence path to cross-check against the direct-collection agents. Building the stack first would produce dashboards with nothing meaningful behind them.

**Verify:** generate a synthetic Windows Application error event via PowerShell; confirm the Windows Agent detects it. Confirm Grafana/Loki signal is consistent with what Docker/K8s agents already reported directly.

---

## Phase 6 — Days 26-30 (buffer into week 6): Hardening pass

**Goal:** turn the working pipeline into something a real user could rely on without hand-holding.

- **Day 26:** JWT auth for dashboard users (login, `users` table, protected frontend routes); API key auth retained for service-to-service `/investigate` triggers (e.g. an alert webhook).
- **Day 27:** Rate limiting, request/response validation review, secrets hygiene (`.env.example`, no committed secrets), dependency pinning.
- **Day 28:** Test suite consolidation — pytest unit tests per agent (mocked SDK clients) + a GitHub Actions CI workflow running a full integration test against a real broken docker-compose stack (dogfooding the Deployment Agent's own data source).
- **Day 29:** Documentation pass — `docs/architecture.md` (LangGraph shape, evidence schema, sequence diagrams), a "how to add a new agent" contributor doc, deployment instructions.
- **Day 30 (buffer):** Chaos pass — trigger container crash + bad deploy + DB outage + CPU spike simultaneously; confirm graceful degradation (no crash, coherent root cause, correct partial-evidence flags); fix what breaks; tag v0.1.

**If you only have 4 weeks, not 6:** merge Phase 4+5 (keep RAG + one of Linux/Network/Windows, drop the other two as stretch goals); reduce Phase 6 to auth + tests only (skip the dedicated docs day and full chaos pass — do one break-it-and-check instead).

---

## Explicitly deferred (README → post-plan roadmap)

| README item | Status |
|---|---|
| BeyondTrust PAM Integration | Deferred |
| Active Directory Integration | Deferred |
| AWS CloudWatch / Azure Monitor / GCP Monitoring | Deferred (local-only scope) |
| ServiceNow Integration | Deferred |
| Slack / Microsoft Teams notifications | Deferred (easy first post-plan add once reports exist) |
| Automatic rollback suggestions | Deferred (recommendations stay text-only advice) |
| Predictive incident detection | Deferred (needs historical trend modeling beyond scope) |
| AI auto-remediation | Deferred — intentionally excluded even long-term unless explicitly revisited (safety: investigation only, no automated write actions against infra) |
| Multi-cloud support | Deferred |
| Full Windows Security Log / AD-integrated audit correlation | Deferred — only light Application/System event log in-plan |
| Jenkins / GitLab CI integration | Deferred — GitHub Actions only in-plan |
| MySQL / MongoDB support | Deferred — Postgres only in-plan |
| SSO/OIDC, multi-tenant auth, HA/clustering | Deferred — JWT + API key only |
| Full conversational AI chat assistant with memory | Deferred — single-turn `/chat` only in-plan |
| Distributed tracing / SLO dashboards | Deferred — structured logging + correlation IDs only |

---

## Initial files to create (Phase 1, Day 1-3)

- `backend/app/main.py`
- `agents/coordinator/state.py`
- `agents/coordinator/graph.py`
- `agents/docker/agent.py`
- `database/models.py`
