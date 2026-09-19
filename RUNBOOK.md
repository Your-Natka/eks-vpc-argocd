Production Support Runbook

1. Purpose

Цей runbook описує типові operational процедури для MLOps production platform.

Основні компоненти:

FastAPI inference;

MLflow Tracking;

MLflow Model Registry;

Blue-Green deployment;

Prometheus;

Grafana;

Loki;

Grafana Alloy;

Evidently;

ArgoCD;

GitLab CI / training workflow.

2. Model lifecycle

Production model reference:

models:/iris-logistic-regression@production

Перевірка Registry version:

import mlflow

mlflow.set_tracking_uri("http://localhost:5000")
client = mlflow.MlflowClient()

version = client.get_model_version_by_alias(
"iris-logistic-regression",
"production",
)

print(version.version)
print(version.run_id)

3. Promote a model

Приклад promotion:

client.set_registered_model_alias(
"iris-logistic-regression",
"staging",
"5",
)

client.set_registered_model_alias(
"iris-logistic-regression",
"production",
"5",
)

Перед production promotion перевіряються:

accuracy;

loss;

data quality;

staging health;

latency;

error rate.

4. FastAPI health check

curl http://127.0.0.1:8000/health

Expected:

{"status":"ok"}

5. Prediction request

curl -X POST http://127.0.0.1:8000/predict \
 -H "Content-Type: application/json" \
 -d '{"features":[5.1,3.5,1.4,0.2]}'

6. API validation

The API requires exactly four numeric features.

Invalid examples:

{"features":[1,2]}

{"features":[12,3,1,0.2]}

Expected result: validation error.

7. Rate limiting

Current application limit:

30 requests / 60 seconds / client IP

Expected HTTP status after exceeding the limit:

429

8. Prometheus metrics

curl http://127.0.0.1:8000/metrics

Main custom metrics:

inference_requests_total
inference_request_latency_seconds

Training metrics from PushGateway:

mlflow_accuracy
mlflow_loss

9. Audit logs

FastAPI writes structured JSON audit events to stdout.

Example fields:

{
"event":"http_request",
"method":"POST",
"path":"/predict",
"status":200,
"client_ip":"127.0.0.1",
"duration_ms":12.3
}

Grafana Alloy is configured to collect Kubernetes logs and send them to Loki.

10. Blue-Green deployment

Production resources:

final/deployment/blue-green/

Active traffic is controlled by the Service selector.

Blue:

selector:
app: inference
color: blue

Green:

selector:
app: inference
color: green

11. Blue → Green switch

Validate Green deployment.

Update Service selector from blue to green.

Commit the change.

Allow ArgoCD to synchronize.

Verify /health and prediction results.

Verify metrics and logs.

12. Rollback

Model rollback

Move MLflow production alias to previous stable version:

client.set_registered_model_alias(
"iris-logistic-regression",
"production",
"<PREVIOUS_VERSION>",
)

Deployment rollback

Restore Service selector to the previous color and synchronize ArgoCD.

13. ArgoCD troubleshooting

List Applications:

kubectl get applications -n infra-tools

Inspect one Application:

kubectl describe application inference-production -n infra-tools

Check Application Controller:

kubectl logs -n infra-tools deployment/argocd-application-controller

14. MLflow troubleshooting

Port-forward:

kubectl port-forward -n mlflow svc/mlflow 5000:5000

Check version:

curl http://localhost:5000/version

Expected response:

3.3.2

15. PushGateway troubleshooting

Port-forward:

kubectl port-forward -n monitoring svc/prometheus-pushgateway 9091:9091

Check service:

curl http://localhost:9091/

16. Loki / Alloy troubleshooting

Check ArgoCD Applications:

kubectl get applications -n infra-tools | grep -E 'loki|alloy'

Check Loki pods:

kubectl get pods -n loki

Check Alloy pods:

kubectl get pods -n alloy

Inspect Alloy logs:

kubectl logs -n alloy -l app.kubernetes.io/name=alloy

17. Evidently drift monitoring

The monitoring script is located at:

monitoring/evidently/evaluate_drift.py

Example:

python3 monitoring/evidently/evaluate_drift.py \
 --reference data/reference.csv \
 --current data/current.csv \
 --output monitoring/evidently/drift-report.html

The datasets must contain a prediction column.

The report contains:

data drift;

prediction drift.

18. High latency response

Check:

request latency;

CPU usage;

memory usage;

model loading;

request volume;

pod restarts.

19. High error rate response

Check:

FastAPI logs;

MLflow availability;

input validation failures;

model loading errors;

pod readiness/liveness;

recent model version.

20. Drift response

When drift is detected:

confirm the drift report;

inspect reference/current distributions;

inspect prediction distribution;

compare model metrics;

investigate data quality;

retrain if necessary;

validate candidate in staging;

promote only after validation.

21. Security checks

Production inference should satisfy:

non-root execution;

seccomp RuntimeDefault;

no privilege escalation;

dropped capabilities;

read-only root filesystem;

writable /tmp only through emptyDir;

dedicated ServiceAccount;

disabled automatic ServiceAccount token mounting;

NetworkPolicy;

ResourceQuota;

input validation;

rate limiting.

22. Cleanup

After collecting screenshots and artifacts:

terraform destroy

The operator must verify that billable cloud resources are removed.

23. Current AWS limitation

The AWS account used during development became unavailable before final runtime verification.

Therefore the procedures in this runbook describe the intended operational workflow and previously verified commands, while the final live AWS environment is currently unavailable for re-execution.
