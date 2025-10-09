# Secrets Rotation Playbook

## Overview

The Datacue backend consumes several sensitive credentials, notably the Groq API key for the Knowledge Agent and the MongoDB connection string used by the model registry. All secrets **must** be sourced from a managed secret store (AWS Secrets Manager, Google Secret Manager, or HashiCorp Vault) and injected as environment variables at runtime. `.env` files are for local development only and may not be checked into source control.

## Rotation Policy

- **Interval:** Rotate every **30 days** or immediately after any suspected compromise.
- **Responsible Team:** Platform Operations (on-call engineer owns execution, service owner validates post-rotation).
- **Tracking:** Log each rotation in the internal change management system, referencing the JIRA ticket ID and the updated secret version/ARN.

## Standard Rotation Procedure

1. **Create new secret version** in the chosen manager with the replacement value.
2. **Update staging environment** configuration to read the new secret version.
3. **Deploy to staging** and smoke-test orchestrator flows (`/ingestion/upload`, `/dashboard/generate`, `/knowledge/analyze`, `/prediction/train`).
4. **Promote to production** by updating the production secret reference or version label (e.g., `AWSCURRENT`).
5. **Redeploy workloads** (Kubernetes pods, ECS tasks, etc.) picking up the new environment values.
6. **Invalidate cached credentials** (restart long-running workers, ensure Celery/FastAPI instances reload config).
7. **Update runbook log** with timestamp, operator, and verification notes.

## Emergency Revocation

- Immediately mark the compromised secret version as disabled or delete it outright.
- Issue a hotfix deploy that references a newly minted secret value.
- Invalidate any active sessions or tokens that may rely on the breached secret (e.g., revoke MongoDB user credentials, revoke Groq API token).
- Run targeted logs search for suspicious activity during the incident window.
- File an incident report and schedule a postmortem within 48 hours.

## Local Development Guidance

- Developers obtain temporary secrets via secure developer vault access.
- Store secrets in a local `.env` file ignored by git; never commit sample keys.
- When rotation occurs, announce on the engineering Slack channel with the new secret retrieval instructions.

Maintaining this rotation discipline prevents stale credentials, limits blast radius during incidents, and aligns the platform with production-security expectations.
