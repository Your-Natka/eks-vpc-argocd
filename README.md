# MLOps Production Platform

## Опис проєкту

Цей проєкт реалізує production-oriented MLOps platform для автоматизованого навчання, реєстрації, контрольованого розгортання та моніторингу ML-моделей.

Платформа об'єднує компоненти, реалізовані в попередніх домашніх завданнях, та розширює їх до повного end-to-end workflow.

Основний pipeline:

```text
Git commit / scheduled trigger
            │
            ▼
       GitLab CI/CD
            │
            ▼
   AWS Step Functions
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
      ┌─────┴─────┐
      │           │
   Staging    Production
                  │
                  ▼
             Kubernetes
                  │
          ┌───────┴───────┐
          │               │
       Inference       Monitoring
          │               │
       FastAPI       Prometheus
          │            Grafana
          │             Loki
          │           Evidently
          ▼
       Predictions
```

## 1. Цілі проєкту

Платформа повинна забезпечувати:

- автоматизований запуск training workflow;
- traceability між Git commit, pipeline, training run та model version;
- реєстрацію моделей у MLflow Model Registry;
- контрольований перехід моделей `Staging → Production`;
- безпечне розгортання моделей у Kubernetes;
- можливість rollback;
- технічний та model-level monitoring;
- базовий security baseline;
- GitOps deployment через ArgoCD;
- відтворюване створення інфраструктури через Terraform;
- документацію для deployment та support.

## 2. Architecture

Основні компоненти платформи:

- AWS VPC;
- AWS EKS;
- AWS S3;
- AWS IAM;
- AWS ECR;
- AWS Step Functions;
- AWS Lambda;
- Terraform;
- Kubernetes;
- Helm;
- ArgoCD;
- MLflow;
- PostgreSQL;
- MinIO / S3-compatible artifact storage;
- Prometheus;
- Grafana;
- Loki;
- Evidently AI;
- FastAPI;
- Docker;
- GitLab CI/CD.

### High-level architecture

```text
                    Git
                     │
                     ▼
              GitLab CI/CD
                     │
                     ▼
             AWS Step Functions
                     │
                     ▼
              Training workflow
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
    MLflow Tracking        Model artifacts
          │                     │
          └──────────┬──────────┘
                     ▼
            MLflow Model Registry
                     │
              Staging / Production
                     │
                     ▼
                   ECR
                     │
                     ▼
                  ArgoCD
                     │
                     ▼
                  EKS
             ┌───────┴────────┐
             │                │
          Staging         Production
             │                │
             └───────┬────────┘
                     ▼
               FastAPI model
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
     Prometheus    Loki      Evidently
          │          │          │
          └──────────┼──────────┘
                     ▼
                  Grafana
```

## 3. Repository structure

```text
eks-vpc-argocd/
│
├── README.md
├── RUNBOOK.md
├── ADR.md
│
├── vpc/
│
├── eks/
│
├── terraform/
│   └── ...
│
├── argocd/
│   ├── applications/
│   ├── charts/
│   └── crds/
│
├── experiments/
│   ├── requirements.txt
│   └── train_and_push.py
│
├── models/
│
├── best_model/
│
├── screens/
│
└── ...
```

Структура буде розширюватися відповідно до реалізації фінального проєкту.

## 4. Infrastructure

AWS infrastructure створюється та керується Terraform.

Основні компоненти:

- VPC;
- EKS cluster;
- Kubernetes node groups;
- IAM roles;
- S3;
- ECR;
- Step Functions;
- Lambda;
- необхідні security та access policies.

Deployment infrastructure повинен бути відтворюваним з чистого стану.

### Terraform workflow

```bash
terraform init
terraform validate
terraform plan
terraform apply
```

Конкретні Terraform directories та порядок bootstrap описані нижче та будуть доповнені відповідно до фінальної структури.

## 5. Kubernetes

Для проєкту використовується один EKS cluster.

Основні namespaces:

```text
staging
production
mlops-system
monitoring
```

### Namespace ownership

| Namespace      | Призначення                                        |
| -------------- | -------------------------------------------------- |
| `staging`      | тестування нових model versions                    |
| `production`   | production inference                               |
| `mlops-system` | MLOps platform components                          |
| `monitoring`   | Prometheus, Grafana, Loki та monitoring components |

## 6. GitOps

Усі Kubernetes deployments виконуються через ArgoCD.

Production принцип:

```text
Git repository
      │
      ▼
    ArgoCD
      │
      ▼
 Kubernetes
```

Ручні `kubectl apply` та `helm install` не використовуються як основний deployment mechanism.

Bootstrap-операції, необхідні для створення самого ArgoCD та базової infrastructure, будуть описані в deployment documentation.

## 7. MLflow Model Registry

MLflow використовується для:

- tracking training runs;
- зберігання metrics;
- зберігання parameters;
- збереження model artifacts;
- versioning моделей;
- управління model lifecycle.

Кожен успішний training run повинен створювати нову model version.

Для кожної версії зберігається metadata:

- Git commit SHA;
- dataset version/hash;
- training parameters;
- evaluation metrics;
- training run reference.

Lifecycle:

```text
Training
   │
   ▼
MLflow Run
   │
   ▼
Model Registry
   │
   ▼
Staging
   │
   ▼
Production
```

## 8. Model promotion

Нова модель спочатку потрапляє у `Staging`.

Перехід у `Production` виконується окремою контрольованою дією.

Production model може бути замінена на нову version після перевірки:

- model metrics;
- data quality;
- deployment health;
- inference latency;
- error rate;
- drift indicators.

Попередня production version повинна залишатися доступною для rollback.

## 9. Model deployment strategy

Для production deployment використовується контрольована deployment strategy.

Обрана стратегія та її trade-offs будуть описані в `ADR.md`.

Deployment повинен забезпечувати:

- одночасне існування старої та нової model version або контрольований traffic split;
- перевірку нової версії;
- можливість збільшення traffic;
- rollback у разі проблем.

## 10. Inference service

ML model надається через REST API на базі FastAPI.

API повинен підтримувати:

- prediction endpoint;
- input validation;
- health check;
- structured logging;
- Prometheus metrics;
- meaningful HTTP errors.

Приклад:

```text
POST /predict
GET  /health
```

Model version, яка використовується inference service, повинна бути traceable до MLflow Model Registry.

## 11. Security baseline

Security є частиною deployment lifecycle.

Основні controls:

- input validation;
- schema enforcement;
- rate limiting;
- Kubernetes RBAC;
- least privilege IAM;
- secrets management;
- immutable model artifacts;
- SHA256 checksum validation;
- audit logging;
- container/image scanning;
- non-root containers;
- network restrictions;
- rollback capability.

### Kubernetes RBAC

Передбачені ролі:

```text
mlops-engineer
viewer
```

`mlops-engineer` має повний доступ до staging та обмежений доступ до production.

`viewer` має read-only доступ.

## 12. Immutable model artifacts

Production model artifact повинен мати:

- version;
- SHA256 checksum;
- provenance;
- model registry reference.

Mutable artifacts типу:

```text
latest.pt
latest.pkl
latest.joblib
```

не використовуються як production source of truth.

Перед deployment inference service повинен перевіряти integrity artifact.

## 13. Audit logging

Критичні model lifecycle actions повинні бути traceable.

Зокрема:

- model registration;
- creation of model version;
- transition to Staging;
- transition to Production;
- archival;
- deletion;
- deployment;
- rollback.

Audit events зберігаються у structured format та доступні через logging infrastructure.

## 14. Observability

Для monitoring використовуються:

- Prometheus;
- Grafana;
- Loki;
- Evidently AI.

### Technical metrics

Потрібно контролювати:

- request rate;
- latency p50;
- latency p95;
- error rate;
- pod CPU;
- pod memory.

### Logs

Inference logs повинні бути structured та доступні через Loki.

### Grafana

Grafana використовується як основний monitoring dashboard.

Dashboard повинен дозволяти швидко визначити:

- чи працює inference service;
- чи зростає latency;
- чи зростає error rate;
- чи є проблеми з ресурсами;
- яка model version обробляє requests.

## 15. Model quality monitoring

Evidently використовується для контролю model/data quality.

Основна задача:

```text
Reference dataset
        │
        ▼
Production data
        │
        ▼
Evidently
        │
        ▼
Drift metrics
        │
        ▼
Prometheus / Grafana
```

За наявності drift повинна запускатися documented response procedure.

## 16. CI/CD

GitLab CI/CD використовується для автоматизації ML workflow.

Pipeline повинен забезпечувати:

```text
Git event
   │
   ▼
CI pipeline
   │
   ▼
Training
   │
   ▼
Model registration
   │
   ▼
Staging
```

Git context передається між pipeline components для забезпечення traceability.

Основні identifiers:

```text
CI_COMMIT_SHORT_SHA
CI_COMMIT_BRANCH
CI_PIPELINE_ID
```

## 17. AWS Step Functions

AWS Step Functions використовується як orchestration layer для training workflow.

Попередньо реалізований workflow:

```text
ValidateData
      │
      ▼
LogMetrics
```

У фінальному проєкті workflow буде розширено відповідно до повного training та model lifecycle.

## 18. Documentation

Проєкт містить:

### README.md

Містить:

- architecture;
- repository structure;
- dependencies;
- infrastructure deployment;
- Kubernetes structure;
- основні компоненти системи.

### RUNBOOK.md

Містить operational procedures:

- deploy new model;
- promote model;
- rollback;
- troubleshooting;
- latency response;
- error-rate response;
- drift response;
- infrastructure cleanup.

### ADR.md

Містить architectural decisions:

- deployment strategy;
- trade-offs;
- alternatives;
- decisions щодо production architecture.

## 19. Deployment from scratch

Фінальна система повинна бути відтворюваною з clean state.

Основний принцип:

```text
Terraform
   │
   ▼
AWS infrastructure
   │
   ▼
EKS
   │
   ▼
ArgoCD
   │
   ▼
MLOps services
   │
   ▼
Inference + Monitoring
```

Точний порядок bootstrap та verification commands буде наведений після завершення infrastructure integration.

## 20. Rollback

Rollback повинен виконуватися однією documented action:

```text
Production model
      │
      ▼
Previous stable version
```

Rollback може бути реалізований через:

- Git commit;
- model version change;
- deployment rollback;

залежно від обраної deployment strategy.

## 21. Cost management

AWS resources використовуються лише на час роботи та демонстрації проєкту.

Після завершення перевірок production infrastructure повинна бути видалена:

```bash
terraform destroy
```

Перед cleanup необхідно переконатися, що всі необхідні screenshots та artifacts для submission збережені.

## 22. Definition of Done

Фінальний проєкт вважається завершеним, якщо:

- [ ] infrastructure створюється через Terraform;
- [ ] EKS cluster працює;
- [ ] необхідні namespaces створені;
- [ ] ArgoCD працює;
- [ ] MLflow працює;
- [ ] Model Registry працює;
- [ ] training створює нову model version;
- [ ] model переходить у Staging;
- [ ] production promotion працює;
- [ ] deployment strategy працює;
- [ ] rollback працює;
- [ ] FastAPI inference працює;
- [ ] input validation працює;
- [ ] rate limiting реалізований;
- [ ] Kubernetes RBAC налаштований;
- [ ] model artifacts immutable;
- [ ] checksum validation реалізована;
- [ ] audit logging працює;
- [ ] Prometheus збирає metrics;
- [ ] Grafana dashboard працює;
- [ ] Loki отримує inference logs;
- [ ] model/data drift monitoring реалізований або задокументований відповідно до обраного scope;
- [ ] README.md завершений;
- [ ] RUNBOOK.md завершений;
- [ ] ADR.md завершений;
- [ ] secrets відсутні в Git repository;
- [ ] фінальний `terraform destroy` успішний.

## 23. Project status

Фінальний проєкт розвивається на окремій Git-гілці:

```text
final-project
```

Гілка базується на завершеному стані попередніх домашніх завдань.

Попередня реалізація ДЗ1–ДЗ10 використовується як foundation та поступово інтегрується у production-oriented MLOps platform.
