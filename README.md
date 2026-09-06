# MLOps Homework №10 — Інтеграція GitLab CI з AWS Step Functions

## Опис проєкту

У межах домашнього завдання реалізовано автоматизацію запуску ML training workflow за допомогою **GitLab CI/CD**, **AWS Step Functions** та **AWS Lambda**.

Інфраструктура AWS створюється та керується за допомогою **Terraform**.

Основна логіка побудована таким чином:

```text
GitLab CI
    │
    │ aws stepfunctions start-execution
    │
    ▼
AWS Step Functions
    │
    ├── ValidateData
    │       │
    │       ▼
    │   Lambda: validate
    │
    └── LogMetrics
            │
            ▼
        Lambda: log_metrics
```

GitLab CI передає до Step Functions Git-контекст поточного pipeline:

- `source`;
- `commit`;
- `branch`;
- `pipeline_id`.

Це дозволяє пов'язати конкретний запуск training workflow з версією коду та GitLab pipeline, який його запустив.

---

# 1. Структура проєкту

Основний GitHub-репозиторій:

```text
eks-vpc-argocd/
```

Для цього домашнього завдання використовується гілка:

```text
lesson-10
```

Структура Terraform:

```text
eks-vpc-argocd/
│
└── terraform/
    ├── main.tf
    ├── data.tf
    ├── terraform.tf
    ├── variables.tf
    ├── outputs.tf
    │
    └── lambda/
        ├── validate.py
        ├── validate.zip
        ├── log_metrics.py
        └── log_metrics.zip
```

GitLab CI зберігається в окремому приватному репозиторії:

```text
mlops-pipeline-10/
│
└── .gitlab-ci.yml
```

GitLab-репозиторій використовується тільки для CI/CD pipeline, який запускає вже створений AWS Step Functions workflow.

---

# 2. Використані технології

- AWS
- AWS Lambda
- AWS Step Functions
- AWS IAM
- Terraform
- GitHub
- GitLab
- GitLab CI/CD
- AWS CLI
- Python

---

# 3. AWS Region

У проєкті використовується AWS region:

```text
eu-north-1
```

Terraform variable:

```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-north-1"
}
```

---

# 4. AWS Lambda

У workflow використовуються дві Lambda-функції.

## Validate Lambda

Файл:

```text
terraform/lambda/validate.py
```

Код:

```python
def handler(event, context):
    print("Validating input data...")

    return {
        "status": "valid"
    }
```

Lambda виконує перевірку вхідних даних та повертає статус:

```json
{
  "status": "valid"
}
```

---

## Log Metrics Lambda

Файл:

```text
terraform/lambda/log_metrics.py
```

Код:

```python
def handler(event, context):
    print("Logging metrics...")

    return {
        "status": "logged"
    }
```

Lambda імітує логування metrics та повертає:

```json
{
  "status": "logged"
}
```

---

# 5. Lambda ZIP packages

Для deployment Lambda використовуються ZIP-архіви:

```text
terraform/lambda/validate.zip
terraform/lambda/log_metrics.zip
```

ZIP-файли створюються командами:

```bash
cd terraform/lambda

zip validate.zip validate.py
zip log_metrics.zip log_metrics.py
```

Таким чином кожна Lambda має окремий deployment package.

---

# 6. Terraform

Terraform використовується для автоматичного створення AWS infrastructure.

Основні Terraform-файли:

```text
terraform/
├── main.tf
├── data.tf
├── terraform.tf
├── variables.tf
└── outputs.tf
```

Terraform створює:

1. IAM role для Lambda;
2. IAM policy attachment для Lambda;
3. Lambda `mlops-training-validate`;
4. Lambda `mlops-training-log-metrics`;
5. IAM role для Step Functions;
6. IAM policy для виклику Lambda з Step Functions;
7. AWS Step Functions state machine `MLOpsPipeline`.

---

# 7. Terraform deployment

Перед виконанням Terraform необхідно мати налаштований AWS CLI profile.

У цьому проєкті використовується profile:

```text
NatkaMLOps
```

Перевірка AWS credentials:

```bash
aws configure list --profile NatkaMLOps
```

Перевірка AWS account:

```bash
aws sts get-caller-identity --profile NatkaMLOps
```

Перехід у Terraform directory:

```bash
cd terraform
```

Ініціалізація Terraform:

```bash
terraform init
```

Перевірка configuration:

```bash
terraform validate
```

Створення plan:

```bash
terraform plan
```

Застосування configuration:

```bash
terraform apply
```

У результаті Terraform створює всі необхідні AWS resources.

---

# 8. AWS Lambda ARNs

Після deployment Terraform повертає ARNs Lambda-функцій.

### Validate Lambda

```text
arn:aws:lambda:eu-north-1:650830975789:function:mlops-training-validate
```

### Log Metrics Lambda

```text
arn:aws:lambda:eu-north-1:650830975789:function:mlops-training-log-metrics
```

---

# 9. AWS Step Functions

Для orchestration використовується AWS Step Functions state machine:

```text
MLOpsPipeline
```

ARN:

```text
arn:aws:states:eu-north-1:650830975789:stateMachine:MLOpsPipeline
```

Workflow виконує Lambda-функції послідовно:

```text
ValidateData
     │
     ▼
validate.handler
     │
     ▼
LogMetrics
     │
     ▼
log_metrics.handler
```

Таким чином друга Lambda запускається після завершення першої.

---

# 10. Step Functions Definition

State machine побудована за принципом послідовного виконання:

```text
ValidateData → LogMetrics
```

Перший state:

```text
ValidateData
```

викликає:

```text
mlops-training-validate
```

Після успішного завершення workflow переходить до:

```text
LogMetrics
```

який викликає:

```text
mlops-training-log-metrics
```

Після завершення `LogMetrics` workflow завершується.

---

# 11. IAM

Для Lambda використовується окрема IAM execution role.

Для Step Functions створена окрема IAM role, яка має permission на виклик обох Lambda-функцій.

Основний permission:

```text
lambda:InvokeFunction
```

Це дозволяє Step Functions виконувати Lambda states.

IAM roles створюються автоматично через Terraform.

---

# 12. Ручний запуск Step Functions

Перед інтеграцією з GitLab CI workflow було перевірено вручну через AWS CLI.

Команда:

```bash
aws stepfunctions start-execution \
  --state-machine-arn "arn:aws:states:eu-north-1:650830975789:stateMachine:MLOpsPipeline" \
  --name "manual-test-$(date +%s)" \
  --input '{"source":"manual","commit":"test","branch":"lesson-10"}'
```

Приклад input:

```json
{
  "source": "manual",
  "commit": "test",
  "branch": "lesson-10"
}
```

Ручний execution був успішно виконаний зі статусом:

```text
SUCCEEDED
```

Це підтверджує коректну роботу Step Functions та обох Lambda-функцій.

---

# 13. GitLab CI/CD

Для автоматичного запуску AWS workflow використовується окремий приватний GitLab repository:

```text
mlops-pipeline-10
```

GitLab pipeline знаходиться у файлі:

```text
.gitlab-ci.yml
```

Pipeline має один stage:

```text
train
```

та один job:

```text
train-model
```

---

# 14. GitLab CI configuration

Файл:

```text
.gitlab-ci.yml
```

містить:

```yaml
stages:
  - train

train-model:
  stage: train
  image:
    name: amazon/aws-cli:2.15.0
    entrypoint: [""]

  script:
    - echo "Starting ML pipeline via AWS Step Functions"
    - |
      aws stepfunctions start-execution \
        --state-machine-arn "$STEP_FUNCTION_ARN" \
        --name "training-${CI_PIPELINE_ID}-${CI_COMMIT_SHORT_SHA}" \
        --input "{\"source\":\"gitlab-ci\",\"commit\":\"${CI_COMMIT_SHORT_SHA}\",\"branch\":\"${CI_COMMIT_BRANCH}\",\"pipeline_id\":\"${CI_PIPELINE_ID}\"}"
```

Docker image:

```text
amazon/aws-cli:2.15.0
```

Використовується AWS CLI для запуску Step Functions.

Параметр:

```yaml
entrypoint: [""]
```

необхідний для того, щоб Docker image не запускав `aws` як власний entrypoint перед виконанням GitLab `script`.

---

# 15. GitLab CI → AWS Step Functions

Під час запуску GitLab pipeline виконується:

```bash
aws stepfunctions start-execution
```

До AWS передається ARN Step Function:

```text
$STEP_FUNCTION_ARN
```

Назва execution формується автоматично:

```text
training-${CI_PIPELINE_ID}-${CI_COMMIT_SHORT_SHA}
```

Наприклад:

```text
training-2824073958-415ae6e1
```

Це дозволяє ідентифікувати execution за GitLab pipeline та commit.

---

# 16. Git-контекст

GitLab CI передає до Step Functions наступний JSON:

```json
{
  "source": "gitlab-ci",
  "commit": "415ae6e1",
  "branch": "main",
  "pipeline_id": "2824073958"
}
```

Використовуються стандартні GitLab CI variables:

```text
CI_COMMIT_SHORT_SHA
CI_COMMIT_BRANCH
CI_PIPELINE_ID
```

### Навіщо передавати commit

`CI_COMMIT_SHORT_SHA` дозволяє пов'язати запуск training workflow з конкретною версією коду.

Наприклад:

```text
Git commit
    │
    ▼
415ae6e1
    │
    ▼
GitLab Pipeline
    │
    ▼
Step Functions Execution
```

Це забезпечує traceability запусків training workflow.

---

# 17. GitLab CI/CD Variables

AWS credentials та інші конфіденційні значення не зберігаються у `.gitlab-ci.yml`.

У GitLab були створені CI/CD Variables:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION
STEP_FUNCTION_ARN
```

### AWS_ACCESS_KEY_ID

Містить AWS Access Key ID.

### AWS_SECRET_ACCESS_KEY

Містить AWS Secret Access Key.

Ця variable зберігається як masked secret.

### AWS_DEFAULT_REGION

Значення:

```text
eu-north-1
```

### STEP_FUNCTION_ARN

Значення:

```text
arn:aws:states:eu-north-1:650830975789:stateMachine:MLOpsPipeline
```

AWS credentials не додаються до Git repository.

---

# 18. GitLab pipeline result

Після налаштування CI/CD variables GitLab pipeline був успішно виконаний.

Pipeline:

```text
2824073958
```

Commit:

```text
415ae6e1
```

GitLab job:

```text
train-model
```

Результат:

```text
Job succeeded
```

У job log AWS CLI повернув execution ARN:

```text
arn:aws:states:eu-north-1:650830975789:execution:MLOpsPipeline:training-2824073958-415ae6e1
```

Також AWS повернув:

```text
startDate: 2026-09-06T10:17:54.107000+00:00
```

Це підтверджує, що GitLab CI успішно викликав AWS Step Functions.

---

# 19. Повний CI/CD flow

Повний workflow домашнього завдання:

```text
Developer
    │
    ▼
GitLab repository
    │
    ▼
GitLab CI/CD
    │
    │ CI_COMMIT_SHORT_SHA
    │ CI_COMMIT_BRANCH
    │ CI_PIPELINE_ID
    │
    ▼
AWS Step Functions
    │
    ▼
ValidateData
    │
    ▼
AWS Lambda
mlops-training-validate
    │
    ▼
LogMetrics
    │
    ▼
AWS Lambda
mlops-training-log-metrics
    │
    ▼
Workflow completed
```

---

# 20. Репозиторії

## GitHub

Основний repository:

```text
eks-vpc-argocd
```

Homework branch:

```text
lesson-10
```

У ньому знаходяться:

```text
Terraform
Lambda
Step Functions
IAM
```

## GitLab

Окремий приватний repository:

```text
mlops-pipeline-10
```

Branch:

```text
main
```

У ньому знаходиться:

```text
.gitlab-ci.yml
```

GitLab repository використовується для CI/CD інтеграції з AWS Step Functions.

---

# 21. Перевірка Lambda

Перевірити створені Lambda:

```bash
aws lambda list-functions \
  --region eu-north-1 \
  --profile NatkaMLOps
```

Очікувані функції:

```text
mlops-training-validate
mlops-training-log-metrics
```

---

# 22. Перевірка Step Functions

Перевірити state machine:

```bash
aws stepfunctions list-state-machines \
  --region eu-north-1 \
  --profile NatkaMLOps
```

Очікувана state machine:

```text
MLOpsPipeline
```

---

# 23. Перевірка Terraform outputs

Після deployment можна перевірити outputs:

```bash
cd terraform

terraform output
```

Очікуються:

```text
validate_lambda_arn
log_metrics_lambda_arn
step_function_arn
```

---

# 24. Результат

У результаті домашнього завдання реалізовано інтеграцію:

```text
GitLab CI
    ↓
AWS Step Functions
    ↓
AWS Lambda
    ↓
Sequential ML workflow
```

Реалізовані основні вимоги:

- створено дві AWS Lambda-функції;
- створено ZIP deployment packages;
- створено IAM roles та permissions;
- створено AWS Step Functions state machine;
- реалізовано послідовний workflow `ValidateData → LogMetrics`;
- Step Functions успішно виконує Lambda;
- Terraform автоматизує створення AWS infrastructure;
- створено окремий GitLab CI pipeline;
- GitLab CI використовує AWS CLI;
- AWS credentials зберігаються у GitLab CI/CD Variables;
- Step Function ARN передається через CI/CD variable;
- GitLab CI передає `CI_COMMIT_SHORT_SHA`;
- GitLab CI передає `CI_COMMIT_BRANCH`;
- GitLab CI передає `CI_PIPELINE_ID`;
- GitLab pipeline успішно запускає AWS Step Functions;
- execution name містить GitLab pipeline ID та commit SHA;
- ручний запуск Step Functions успішно завершився зі статусом `SUCCEEDED`.

---

# 25. Фінальна структура для здачі

### GitHub — branch `lesson-10`

```text
eks-vpc-argocd/
│
├── terraform/
│   ├── main.tf
│   ├── data.tf
│   ├── terraform.tf
│   ├── variables.tf
│   ├── outputs.tf
│   │
│   └── lambda/
│       ├── validate.py
│       ├── validate.zip
│       ├── log_metrics.py
│       └── log_metrics.zip
│
└── README.md
```

### GitLab — branch `main`

```text
mlops-pipeline-10/
│
└── .gitlab-ci.yml
```

---

# 26. Висновок

У рамках домашнього завдання створено повний автоматизований workflow запуску ML training process.

Terraform відповідає за створення AWS infrastructure, AWS Step Functions — за orchestration workflow, Lambda — за виконання окремих етапів, а GitLab CI — за автоматичний запуск workflow.

Git-контекст передається до Step Functions під час кожного запуску, що забезпечує можливість відстежити, з якого commit та якого GitLab pipeline було запущено training workflow.

Фінальна схема:

```text
GitHub
  │
  │ Terraform
  ▼
AWS Infrastructure
  │
  ├── Lambda Validate
  ├── Lambda Log Metrics
  └── Step Functions
          ▲
          │
          │ start-execution
          │
      GitLab CI
          │
          ▼
   Git commit / pipeline
```
