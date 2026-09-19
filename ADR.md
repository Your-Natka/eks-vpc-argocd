Architecture Decision Record

ADR-001 — Blue-Green deployment

Status

Accepted

Context

The final project requires safe deployment of new model versions and fast rollback.

Decision

Use Blue-Green deployment with two Kubernetes Deployments:

inference-blue;

inference-green.

A single Service selects the active color.

Rationale

Blue-Green provides:

simple traffic switching;

isolated environments;

easy rollback;

no additional rollout controller requirement.

ADR-002 — MLflow aliases for model lifecycle

Status

Accepted

Decision

Use MLflow aliases:

staging
production

Production inference loads:

models:/iris-logistic-regression@production

Rationale

The inference application is decoupled from an exact version number. Promotion changes an alias instead of changing application code.

ADR-003 — Iris LogisticRegression as final production model

Status

Accepted

Context

The original inference service from DЗ №1 used MobileNetV2 image inference, while the training pipeline from the later MLOps work produced an Iris LogisticRegression model.

Decision

Use Iris LogisticRegression as the final end-to-end model and change the production inference contract to four numeric Iris features.

Rationale

This creates one coherent lifecycle:

training
↓
MLflow Tracking
↓
Model Registry
↓
production alias
↓
FastAPI

This avoids deploying a model that is incompatible with the actual training pipeline.

ADR-004 — Kubernetes security baseline

Status

Accepted

Decision

The production inference workload uses:

non-root container;

RuntimeDefault seccomp profile;

disabled privilege escalation;

dropped Linux capabilities;

read-only root filesystem;

writable /tmp through emptyDir;

dedicated ServiceAccount;

disabled automatic ServiceAccount token mounting;

NetworkPolicy;

ResourceQuota;

input validation;

rate limiting.

Rationale

These controls provide a practical least-privilege baseline for a Kubernetes inference service.

ADR-005 — Loki and Grafana Alloy

Status

Accepted

Decision

Use Loki as log storage and Grafana Alloy as Kubernetes log collector.

Rationale

The design integrates naturally with Grafana and separates log collection from storage/querying.

ADR-006 — Evidently for drift monitoring

Status

Accepted

Decision

Use Evidently to compare reference and current datasets for:

data drift;

prediction drift.

The workflow produces an HTML drift report.

Rationale

Evidently provides a dedicated model/data quality layer that is separate from infrastructure metrics.

ADR-007 — Model artifacts and provenance

Status

Accepted

Decision

MLflow Model Registry versioning is the production source of truth. Each production model is referenced through a concrete registry version/alias and linked to a training run.

Mutable names such as latest.joblib are not used as the production source of truth.

Rationale

This provides traceability and rollback without depending on mutable artifact filenames.

ADR-008 — AWS deployment limitation

Status

Accepted

Context

The AWS account used during development was closed after Free Tier credits were exhausted.

Decision

Complete the repository-side implementation and document the infrastructure blocker instead of claiming a final live deployment that could not be verified.

Consequence

The repository contains the intended production architecture, code, manifests and documentation. Previously successful AWS/EKS screenshots and test outputs remain valid development evidence, while final runtime verification after account closure is not claimed.
