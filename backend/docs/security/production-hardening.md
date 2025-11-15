# Production Hardening Checklist

This guide lists the security and operational controls required before exposing the DataCue orchestrator publicly. Each section includes concrete next steps and tooling suggestions.

## 1. Authentication & Authorization

- **JWT Auth:**
  - Implement OAuth2 Password Grant with `OAuth2PasswordBearer` in FastAPI.
  - Store hashed credentials in Postgres or Mongo (not environment variables).
  - Rotate signing keys yearly or upon compromise.
- **RBAC Roles:**
  - `analyst` → read-only access to dashboard and knowledge endpoints.
  - `ml_engineer` → analyst plus `/prediction/train`, `/prediction/models`.
  - `admin` → full access including `/orchestrator/pipeline`, credential management.
- **Enforcement:**
  - Add dependency injection wrapper that validates JWT claims before hitting service methods.
  - Log authorization failures with user ID and endpoint.

## 2. Rate Limiting & Job Control

- **Rate Limiting:**
  - Integrate [`fastapi-limiter`](https://github.com/long2ice/fastapi-limiter) backed by Redis.
  - Suggested limits:
    - `/ingestion/upload`: 20 req/hour per user.
    - `/prediction/train`: 5 req/day per project.
    - `/knowledge/analyze`: 60 req/hour per user.
- **Background Jobs:**
  - Move long-running training/LLM tasks to Celery or RQ workers.
  - Store job metadata in Redis; expose `/jobs/{id}` for status polling.
  - Enforce per-job timeout (e.g., 30 minutes) and auto-retry policies.

## 3. Monitoring, Metrics, and Logging

- **Metrics:**
  - Expose Prometheus metrics via `/metrics` (use `prometheus-fastapi-instrumentator`).
  - Track: request latency, success/failure counts, queue depth, models archived, LLM token usage.
- **Dashboards:**
  - Build Grafana panels for latency percentiles, error rates, queue length, disk usage.
  - Configure alerts to PagerDuty/Slack when thresholds exceeded.
- **Logs:**
  - Ship structured JSON logs to ELK/OpenSearch via Filebeat/Fluent Bit.
  - Include request ID, user ID, dataset name/model ID, and job ID in log context.

## 4. CI/CD & Testing Enhancements

- **Pipeline:**
  - Use GitHub Actions (or GitLab CI) with stages: lint, test, security scan, build, deploy.
  - Commands per stage: `ruff`/`flake8`, `black --check`, `pytest`, `bandit`, `pip-audit`.
- **Test Coverage:**
  - Unit tests per agent module.
  - Integration tests covering orchestrator pipeline with mocked Groq/Mongo.
  - Regression datasets to ensure dashboards, insights, predictions remain stable.
  - Contract tests verifying API schemas (pydantic models vs OpenAPI spec).

## 5. Load and Resilience Testing

- **Tools:** Use `locust` or `k6` to simulate concurrent uploads, predictions, pipeline runs.
- **Goals:**
  - Sustain 50 concurrent pipeline requests with <5% error rate.
  - Measure CPU/Memory usage; adjust autoscaling thresholds accordingly.
  - Validate circuit breakers and graceful degradation when queue saturated.

## 6. Security Scanning & Dependency Hygiene

- **Dependencies:** Enable Dependabot or Renovate to monitor `requirements*.txt`.
- **Static Analysis:** Run Bandit or Semgrep in CI; fail builds on high-severity findings.
- **Container Scanning:** Integrate Trivy or Grype to scan Docker images pre-deploy.
- **Patch Cadence:** Document monthly updates for base images, Python runtime, and libraries. Track CVEs via security mailing lists.

## 7. Incident Response & Alerting

- Define on-call rotation and escalation path.
- Automate alerts for:
  - Multiple authentication failures (possible brute force).
  - Model drift metrics crossing thresholds.
  - Disk usage >80% on persistent volumes.
  - Backup job failures or skipped runs.
- Maintain runbooks for common incidents (Mongo outage, Groq API throttling, volume exhaustion).

Following this checklist closes the remaining gaps around security, resiliency, and observability required for a public launch.
