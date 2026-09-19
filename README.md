MLOps Production Platform

Опис проєкту

Цей проєкт реалізує production-oriented MLOps platform для автоматизованого навчання, реєстрації, контрольованого розгортання та моніторингу ML-моделі.

Платформа об'єднує напрацювання попередніх домашніх завдань та розширює їх компонентами Model Registry, deployment strategy, security baseline та observability.

Основний workflow:

Git commit / scheduled trigger
│
▼
GitLab CI/CD
│
▼
Training workflow
│
▼
MLflow Tracking
│
▼
MLflow Model Registry
│
┌────┴────┐
▼ ▼
Staging Production
│
▼
Kubernetes
│
┌─────┴─────┐
▼ ▼
FastAPI Monitoring
│
┌──────────┼──────────┐
▼ ▼ ▼
Prometheus Loki Evidently
│ │ │
└──────────┴──────────┘
▼
Grafana

1. Цілі проєкту

Платформа повинна забезпечувати:

автоматизований запуск training workflow;

traceability між Git context, pipeline, training run та model version;

реєстрацію моделей у MLflow Model Registry;

контрольований перехід моделі у Staging та Production;

безпечне розгортання моделі у Kubernetes;

Blue-Green deployment та rollback;

технічний та model-level monitoring;

базовий security baseline;

GitOps deployment через ArgoCD;

відтворювану інфраструктуру через Terraform;

документацію для deployment та support.

2. Architecture

Основні компоненти

AWS VPC;

AWS EKS;

AWS ECR;

AWS S3 / S3-compatible storage;

AWS IAM;

AWS Step Functions;

AWS Lambda;

Terraform;

Kubernetes;

Helm;

ArgoCD;

MLflow;

PostgreSQL;

MinIO / S3-compatible artifact storage;

Prometheus;

Grafana;

Loki;

Grafana Alloy;

Evidently AI;

FastAPI;

Docker;

GitLab CI/CD.

High-level architecture

                         Git
                          │
                          ▼
                    GitLab CI/CD
                          │
                          ▼
                 Training / orchestration
                          │
                          ▼
                   MLflow Tracking
                          │
                          ▼
                MLflow Model Registry
                          │
                 staging / production
                          │
                          ▼
                     FastAPI
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
        Prometheus       Loki       Evidently
             │            │            │
             └────────────┼────────────┘
                          ▼
                       Grafana

3. Final model architecture

Початкова inference-служба ДЗ №1 використовувала MobileNetV2 та image upload. У фінальному проєкті inference-контракт уніфіковано з training pipeline і MLflow Registry.

Фінальна модель:

iris-logistic-regression

Production model URI:

models:/iris-logistic-regression@production

API приймає чотири числові Iris features.

Приклад:

{
"features": [5.1, 3.5, 1.4, 0.2]
}

4. Repository structure

eks-vpc-argocd/
├── README.md
├── RUNBOOK.md
├── ADR.md
├── vpc/
├── eks/
├── terraform/
├── argocd/
│ ├── applications/
│ ├── charts/
│ └── crds/
├── experiments/
│ ├── requirements.txt
│ └── train_and_push.py
├── monitoring/
│ └── evidently/
├── inference/
│ ├── Dockerfile
│ ├── requirements.txt
│ ├── app/
│ └── helm/
├── final/
│ ├── deployment/
│ │ └── blue-green/
│ └── register_model.py
├── models/
├── best_model/
└── screens/

5. Infrastructure

AWS infrastructure створюється через Terraform.

Базовий workflow:

terraform init
terraform validate
terraform plan
terraform apply

Після завершення роботи:

terraform destroy

У поточній submission-версії фактична повторна AWS verification заблокована через закриття AWS account.

6. Kubernetes

Передбачені namespaces:

staging
production
mlflow
monitoring
infra-tools
loki
alloy

Production inference має:

Blue deployment;

Green deployment;

ClusterIP Service;

ResourceQuota;

NetworkPolicy;

dedicated ServiceAccount;

RBAC baseline;

securityContext.

7. GitOps

Основним deployment mechanism є ArgoCD.

Git repository
│
▼
ArgoCD
│
▼
Kubernetes

Production Application:

argocd/applications/inference-production.yaml

Application синхронізує:

final/deployment/blue-green

8. MLflow Model Registry

Training pipeline:

experiments/train_and_push.py

Training:

використовує Iris dataset;

тренує кілька LogisticRegression configurations;

записує parameters;

записує accuracy та log loss;

логую model як MLflow model;

створює нову model version у Registry;

визначає найкращу модель;

записує Prometheus metrics через PushGateway.

Registry model:

iris-logistic-regression

Під час розробки було створено versions 1–6.

Найкращий run:

run: a511ed53aea84e56b79c59186ead56c2
accuracy: 1.0000
C: 10.0
max_iter: 100

Version 5 була призначена aliases:

staging
production

9. Model promotion

Фінальний lifecycle:

Training
│
▼
MLflow Run
│
▼
Model Registry
│
▼
staging alias
│
▼
production alias

Production inference використовує alias, а не hard-coded version number:

models:/iris-logistic-regression@production

Це дозволяє перемикати production model без зміни application code.

10. Blue-Green deployment

Обрана deployment strategy — Blue-Green.

Реалізація:

final/deployment/blue-green/
├── namespace.yaml
├── blue.yaml
├── green.yaml
├── service.yaml
├── serviceaccount.yaml
├── resourcequota.yaml
├── networkpolicy.yaml
└── rbac.yaml

Service selector визначає активний колір:

selector:
app: inference
color: blue

Для перемикання на Green selector змінюється на:

selector:
app: inference
color: green

11. Inference service

FastAPI application:

inference/app/main.py
inference/app/inference.py

Endpoints:

GET /health
POST /predict
GET /metrics

Input validation:

рівно 4 features;

кожна feature у межах 0–10.

Rate limiting:

30 requests / 60 seconds / client IP

Помилки:

400 invalid input
429 rate limit exceeded
500 internal inference error

Audit middleware записує structured JSON events у stdout.

12. Security baseline

Production inference має:

non-root container;

RuntimeDefault seccomp profile;

allowPrivilegeEscalation: false;

dropped Linux capabilities;

readOnlyRootFilesystem: true;

writable /tmp через emptyDir;

dedicated ServiceAccount;

disabled automatic ServiceAccount token mounting;

NetworkPolicy;

ResourceQuota;

input validation;

rate limiting.

Kubernetes RBAC

Для ServiceAccount inference описаний мінімальний Role/RoleBinding baseline для читання model metadata ConfigMap.

13. Immutable model artifacts

Production source of truth — MLflow Model Registry version + alias.

Не використовуються як source of truth:

latest.pt
latest.pkl
latest.joblib

Кожна model version пов'язана з конкретним MLflow run.

14. Audit logging

Inference service записує structured request audit events з полями:

event;

HTTP method;

path;

status;

client IP;

duration.

Логи призначені для подальшого збору Grafana Alloy та зберігання в Loki.

15. Observability

Prometheus

Inference service експонує:

inference_requests_total
inference_request_latency_seconds

Також у попередньому середовищі використовувався PushGateway для training metrics:

mlflow_accuracy
mlflow_loss

Grafana

Grafana використовується для dashboards та Prometheus exploration.

Loki

Для фінального проєкту підготовлено ArgoCD Application для Loki:

argocd/applications/loki.yaml

Grafana Alloy

Підготовлено ArgoCD Application для збору Kubernetes logs:

argocd/applications/alloy.yaml

Alloy forwarding направлений до Loki.

16. Model quality monitoring

Підготовлено Evidently workflow:

monitoring/evidently/evaluate_drift.py

Workflow порівнює:

reference dataset
│
▼
current dataset
│
▼
Evidently
│
┌────┴────┐
▼ ▼
data drift prediction drift

Скрипт генерує HTML drift report.

Синтаксис скрипта локально перевірений через py_compile.

Повторна runtime verification у AWS після закриття account неможлива.

17. CI/CD

GitLab CI використовувався для запуску training workflow через Step Functions.

Traceability identifiers:

CI_COMMIT_SHORT_SHA
CI_COMMIT_BRANCH
CI_PIPELINE_ID

Раніше успішно перевірений workflow:

GitLab CI
│
▼
AWS Step Functions
│
├── ValidateData
│
└── LogMetrics

Фінальна model registration/promotion логіка реалізована в repository; повторна AWS runtime verification зараз недоступна.

18. Документація

Проєкт містить три основні документи:

README.md

Опис архітектури, компонентів, repository structure та deployment approach.

RUNBOOK.md

Operational procedures для model promotion, rollback, monitoring та troubleshooting.

ADR.md

Architecture Decision Records з поясненням ключових рішень.

19. Розгортання

Очікуваний порядок:

Terraform
↓
AWS infrastructure
↓
EKS
↓
ArgoCD
↓
MLflow / PostgreSQL / MinIO
↓
Prometheus / Grafana / Loki / Alloy
↓
Inference
↓
Blue-Green

Основний Terraform lifecycle:

terraform init
terraform validate
terraform plan
terraform apply

20. Rollback

Rollback можливий двома незалежними способами:

Перемістити MLflow production alias на попередню stable version.

Перемкнути Kubernetes Service selector з blue на green або навпаки.

Детальні operational steps наведені у RUNBOOK.md.

21. Cost management

Для AWS рекомендований патерн:

terraform apply
↓
work / demo / screenshots
↓
terraform destroy

Поточна фінальна AWS verification не виконана через блокування account.

22. Визначення готовності

Реалізовано / підготовлено

Terraform infrastructure code

EKS/VPC code foundation

ArgoCD Applications

MLflow Tracking

MLflow Model Registry

model versions

staging alias

production alias

FastAPI inference

input validation

rate limiting

health checks

Prometheus metrics

audit logging middleware

non-root container

Kubernetes securityContext

ServiceAccount baseline

NetworkPolicy

ResourceQuota

RBAC manifests

Blue-Green manifests

Loki ArgoCD manifest

Alloy ArgoCD manifest

Evidently drift script

README

RUNBOOK

ADR

Не підтверджено після блокування AWS

final EKS runtime verification

final production Blue-Green switch in the live cluster

live Loki verification

live Evidently execution in cluster

final end-to-end CI/CD runtime verification

final terraform destroy on the final environment

23. Статус проєкту

Branch:

final-project

Під час розробки була успішно перевірена значна частина AWS/EKS stack, включаючи MLflow, PostgreSQL, MinIO, FastAPI inference та PushGateway.

AWS account був закритий після вичерпання Free Tier credits до повторної фінальної runtime verification. Через це останній production verification не був виконаний.

Це є зовнішнім infrastructure blocker, а не відсутністю реалізації repository-side компонентів.

24. Previously verified local / development access

MLflow

kubectl port-forward -n mlflow svc/mlflow 5000:5000

UI:

http://localhost:5000/

PushGateway

kubectl port-forward -n monitoring svc/prometheus-pushgateway 9091:9091

UI:

http://localhost:9091/

FastAPI

cd inference
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000

Swagger:

http://127.0.0.1:8000/docs

Health:

http://127.0.0.1:8000/health

25. Примітка щодо подання

Цей репозиторій містить реалізовану фінальну архітектуру MLOps та конфігурацію для production середовища.

Остаточну перевірку в AWS не вдалося завершити, оскільки обліковий запис AWS став недоступним перед етапом фінальної інтеграції. Зроблені раніше скріншоти та результати успішних запусків на етапі розробки збережено як підтвердження; screens додані разом із цим репозиторієм.

## Grafana inference dashboard

Фінальний dashboard зберігається як код у:

`monitoring/grafana/inference-dashboard.json`

Dashboard призначений для production inference service та містить:

- request rate;
- latency p50;
- latency p95;
- error rate;
- pod CPU;
- pod memory;
- розподіл HTTP requests за status code.

Kubernetes ConfigMap для GitOps:

`argocd/applications/grafana-dashboard.yaml`

Dashboard розрахований на Prometheus datasource і оновлення кожні 15 секунд.

## 24. Final implementation status

На фінальному етапі проєкту реалізовано та закодовано додаткові production-oriented компоненти.

### Kubernetes namespaces

У GitOps-репозиторії явно визначені чотири основні namespaces:

| Namespace      | Призначення                                        |
| -------------- | -------------------------------------------------- |
| `staging`      | тестування та перевірка нових версій моделей       |
| `production`   | production inference service                       |
| `mlops-system` | системні компоненти MLOps-платформи                |
| `monitoring`   | Prometheus, Grafana, Loki та monitoring components |

Namespace manifests знаходяться у:

```text
final/namespaces/namespaces.yaml
```

ArgoCD Application:

```text
argocd/applications/namespaces.yaml
```

### Grafana inference dashboard

Фінальний dashboard зберігається як version-controlled artifact:

```text
monitoring/grafana/inference-dashboard.json
```

GitOps ConfigMap:

```text
argocd/applications/grafana-dashboard.yaml
```

Dashboard містить:

- request rate;
- latency p50;
- latency p95;
- error rate;
- pod CPU;
- pod memory;
- HTTP requests by status code.

Оновлення dashboard передбачене кожні 15 секунд.

### Model Registry audit logging

Training pipeline генерує structured audit events для:

- реєстрації нової model version;
- переходу моделі до `Staging`.

Promotion script генерує structured events для:

- переходу до `Production`;
- збереження попередньої production version як archived;
- видалення model version;
- помилок promotion operation.

Основний promotion script:

```text
final/promote_model.py
```

Audit events мають JSON-формат та призначені для збору logging infrastructure і подальшого аналізу через Loki.

### Model artifact integrity

Для кожної model version генерується SHA256 checksum.

Checksum:

```text
training artifact
      ↓
SHA256
      ↓
MLflow model version metadata
```

Перед завантаженням production-моделі inference service повторно обчислює checksum.

Якщо фактичний checksum не відповідає значенню, збереженому в MLflow Model Registry, модель не завантажується.

### Kubernetes RBAC

RBAC configuration знаходиться у:

```text
rbac/rbac.yaml
```

Реалізовані ролі:

```text
mlops-engineer
viewer
```

`mlops-engineer` має:

- повний доступ до `staging`;
- read-only доступ до `production`.

`viewer` має read-only доступ до `staging` та `production`.

### Security hardening

Production inference workload використовує:

- non-root container;
- RuntimeDefault seccomp profile;
- `allowPrivilegeEscalation: false`;
- dropped Linux capabilities;
- read-only root filesystem;
- dedicated ServiceAccount;
- disabled automatic ServiceAccount token mounting;
- NetworkPolicy;
- ResourceQuota;
- Pydantic input validation;
- application-level rate limiting.

### Threat model

Threat model знаходиться у:

```text
security/THREAT_MODEL.md
```

Документ описує основні загрози:

- malicious input;
- API abuse;
- unauthorized Kubernetes access;
- model artifact tampering;
- unsafe model promotion;
- inference container compromise;
- недостатню traceability model lifecycle.

Для кожної загрози описані відповідні security controls.

## 25. Bootstrap and GitOps deployment

Для AWS/EKS deployment передбачається поетапний bootstrap:

```text
Phase 1
VPC
  ↓
Phase 2
EKS
  ↓
Phase 3
ArgoCD
  ↓
Phase 4
MLflow / PostgreSQL / MinIO / Prometheus / Grafana / PushGateway / Loki
  ↓
Phase 5
Inference deployment
  ↓
Phase 6
Model promotion
```

Після bootstrap Kubernetes application deployments виконуються через ArgoCD із Git repository.

Ручні `kubectl apply` та `helm install` не використовуються як основний deployment mechanism.

## 26. AWS deployment limitation

Фінальна AWS verification не була завершена через закриття AWS account після вичерпання доступних Free Tier credits.

Через відсутність доступу до EKS неможливо повторно виконати:

- live ArgoCD synchronization;
- production inference verification;
- live Grafana/Loki verification;
- final Blue-Green switch;
- фінальний `terraform destroy`.

Код інфраструктури, Kubernetes manifests, MLflow workflow, security controls, monitoring configuration та documentation збережені у Git repository.

Локальні перевірки YAML, JSON та Python syntax успішно виконані.

Наявні screenshots з попередніх етапів використовуються як evidence для раніше перевірених компонентів.

## 27. Submission artifacts

Фінальний submission включає:

```text
Git repository
├── README.md
├── RUNBOOK.md
├── ADR.md
├── security/THREAT_MODEL.md
├── Terraform
├── Kubernetes manifests
├── Helm configuration
├── ArgoCD Applications
├── MLflow training and promotion workflow
├── FastAPI inference service
├── Monitoring configuration
└── Screenshots
```

Для передачі проєкту також підготовлений архів:

```text
eks-vpc-argocd-final.zip
```

До архіву не включаються Terraform state files, `.terraform` directories, plan files та локальні Python cache files.
