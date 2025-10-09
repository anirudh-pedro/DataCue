# Persistence, Backups, and Retention

## Target Directories

| Path                             | Purpose                                | Action in Production                                                                                     |
| -------------------------------- | -------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `/app/backend/data`              | User-uploaded datasets (CSV/Excel)     | Mount read/write persistent volume (e.g., PVC in K8s, EBS/EFS). Enforce daily virus scan & quota alerts. |
| `/app/backend/saved_models`      | Serialized model artifacts (`.pkl`)    | Persistent volume with encryption at rest. Enable lifecycle rules to archive aged files.                 |
| `/app/backend/metadata`          | Model metadata JSON and registry cache | Persistent volume; maintain consistency with Mongo model registry.                                       |
| `/app/backend/logs` (if enabled) | Application logs                       | Ship to central logging (ELK/Opensearch) or mount to append-only volume.                                 |

> **Note:** Adjust mount paths if container image differs; ensure application config references mounted directories via environment variables.

## Container / Deployment Checklist

- Define persistent volume claims for each directory with adequate IOPS.
- Set `fsGroup` or appropriate permissions so the FastAPI user can read/write the mounts.
- Configure Kubernetes `emptyDir` only for ephemeral caches—never for datasets/models.

## MongoDB Backups

- **Preferred:** MongoDB Atlas continuous backups or point-in-time restores.
- **Self-managed:**
  - Run `mongodump` nightly (UTC 02:00) storing archives in secure object storage (S3/GCS) with 30-day retention.
  - Verify dump completion and size; alert if deviation >15% from baseline.
  - Monthly test restore into staging using `mongorestore` to validate integrity.

## Model Retention Policy

1. Track models by dataset name and timestamp in `ModelRegistry`.
2. For each dataset:
   - Keep **latest 3 successful models** in `saved_models/` and Mongo metadata.
   - Move older artifacts to cold storage (S3 Glacier / GCS Nearline) tagged with dataset and version.
   - Remove local copies after archival confirmation.
3. Implement a scheduled cleanup job (e.g., daily Celery beat task) that:
   - Scans registry entries.
   - Archives and prunes stale models.
   - Logs actions and emits Prometheus metrics (`models_archived_total`).

## Dataset Retention

- Datasets older than 90 days without re-use should be archived to cold storage.
- Maintain checksum manifest for uploaded files to detect corruption.
- Provide tooling to rehydrate datasets into `/data` before re-running pipelines.

## Disaster Recovery

- Document Recovery Time Objective (RTO) and Recovery Point Objective (RPO):
  - RTO ≤ 4 hours.
  - RPO ≤ 24 hours (aligned with daily backups).
- Store infrastructure-as-code and manifest snapshots in version control for rapid redeploy.
- Run quarterly DR drills restoring database, models, and datasets into a clean environment.

Following this policy keeps user assets durable, storage costs predictable, and regulatory requirements satisfied.
