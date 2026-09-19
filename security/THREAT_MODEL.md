# Модель загроз

## 1. Область аналізу

Ця модель загроз охоплює production MLOps-платформу:

```text
GitLab CI
   ↓
MLflow Tracking / Model Registry
   ↓
Model artifact
   ↓
ArgoCD
   ↓
Kubernetes
   ↓
FastAPI inference
   ↓
Prometheus / Loki / Grafana
```

Мета аналізу — визначити основні загрози для ML-моделі, inference API, Kubernetes та процесу розгортання, а також описати реалізовані засоби їх зниження.

---

## 2. Загроза: шкідливий або некоректний input

### Ризик

Атакувальник може надсилати в `/predict` некоректні, неочікувані або екстремальні значення.

Можливі наслідки:

- помилки застосунку;
- перевантаження сервісу;
- некоректна поведінка моделі;
- отримання непередбачуваних результатів.

### Контролі

- Pydantic validation;
- перевірка наявності рівно чотирьох ознак;
- перевірка числових значень;
- обмеження допустимого діапазону ознак;
- осмислені HTTP 400 responses;
- внутрішні деталі exception не повертаються клієнту.

---

## 3. Загроза: зловживання API та request flooding

### Ризик

Атакувальник може надсилати велику кількість запитів до inference endpoint.

Можливі наслідки:

- перевантаження CPU;
- збільшення використання пам'яті;
- зростання latency;
- недоступність inference service.

### Контролі

- application-level rate limiting;
- максимум 30 запитів за 60 секунд для одного client IP;
- HTTP 429 після перевищення ліміту;
- Prometheus metrics для request rate та latency;
- Kubernetes resource requests та limits.

---

## 4. Загроза: несанкціонований доступ до Kubernetes

### Ризик

Скомпрометований користувач або workload може отримати надмірні Kubernetes permissions.

Можливі наслідки:

- зміна production workload;
- видалення ресурсів;
- доступ до інших сервісів;
- розгортання небезпечного контейнера.

### Контролі

У Kubernetes передбачено дві основні ролі:

- `mlops-engineer`;
- `viewer`.

`mlops-engineer` має:

- повний доступ до `staging`;
- read-only доступ до `production`.

`viewer` має:

- read-only доступ до `staging`;
- read-only доступ до `production`.

Додатково використовуються:

- окремий ServiceAccount для inference;
- вимкнене автоматичне монтування ServiceAccount token;
- `runAsNonRoot`;
- `seccompProfile: RuntimeDefault`;
- заборона privilege escalation;
- `capabilities: drop: ALL`;
- read-only root filesystem;
- NetworkPolicy;
- ResourceQuota.

---

## 5. Загроза: зміна або пошкодження model artifact

### Ризик

Model artifact може бути змінений після реєстрації або перед завантаженням у production.

Можливі наслідки:

- запуск пошкодженої моделі;
- запуск зміненої моделі;
- некоректні predictions;
- порушення цілісності ML pipeline.

### Контролі

Під час training:

```text
Model artifact
      ↓
SHA256
      ↓
MLflow Model Version metadata
```

Для кожної model version зберігається `artifact_sha256`.

Під час inference:

```text
Production model
      ↓
download artifact
      ↓
calculate SHA256
      ↓
compare with registered checksum
```

Якщо checksum не збігається, inference service **відмовляється завантажувати модель**.

Це забезпечує перевірку цілісності model artifact перед використанням.

---

## 6. Загроза: несанкціонований або небезпечний promotion моделі

### Ризик

Неправильна model version може бути випадково або навмисно переведена в production.

Можливі наслідки:

- погіршення якості predictions;
- production incident;
- збільшення error rate;
- необхідність термінового rollback.

### Контролі

- MLflow Model Registry;
- окремі aliases `staging` та `production`;
- окремий promotion script;
- попередня production version зберігається;
- попередня production version позначається як `archived`;
- Blue-Green deployment;
- документований rollback;
- audit events під час promotion.

Основний workflow:

```text
Training
   ↓
Model Registry
   ↓
Staging
   ↓
Validation
   ↓
Production
```

---

## 7. Загроза: компрометація inference container

### Ризик

Уразливий container або application dependency може бути використаний для отримання доступу до системи.

Можливі наслідки:

- виконання небезпечних команд;
- escalation of privileges;
- доступ до Kubernetes API;
- зміна application resources.

### Контролі

Inference container працює:

```text
non-root user
```

Додатково:

- `allowPrivilegeEscalation: false`;
- `readOnlyRootFilesystem: true`;
- `capabilities.drop: ALL`;
- `seccompProfile: RuntimeDefault`;
- окремий ServiceAccount;
- `automountServiceAccountToken: false`;
- NetworkPolicy;
- ResourceQuota.

---

## 8. Загроза: недостатній контроль model lifecycle

### Ризик

Без traceability складно визначити:

- хто зареєстрував модель;
- яка version була promoted;
- яка version була production;
- яка версія була замінена;
- коли виконувався rollback.

### Контролі

У training та model lifecycle зберігаються:

- Git commit SHA;
- dataset SHA256;
- model version;
- training run;
- accuracy;
- loss;
- artifact SHA256.

Promotion operations генерують structured audit events.

---

## 9. Audit logging

Критичні операції Model Registry повинні бути traceable:

- registration;
- creation of model version;
- promotion to Staging;
- promotion to Production;
- archival;
- deletion;
- rollback.

Audit events мають структурований JSON-формат і можуть передаватися через logging infrastructure до Loki.

Приклад події:

```json
{
  "event": "model_promotion",
  "model_name": "iris-logistic-regression",
  "version": "5",
  "previous_version": "4",
  "actor": "manual",
  "status": "success"
}
```

---

## 10. Залишкові ризики

Поточна реалізація все ще залежить від безпеки:

- GitLab credentials;
- MLflow administrator credentials;
- Kubernetes administrative access;
- cloud account credentials.

Для повноцінного production environment додатково бажано використовувати:

- зовнішній secrets manager;
- container vulnerability scanning;
- signed container images;
- централізовану identity management систему;
- rotation credentials;
- захищений ingress;
- регулярний security audit.

---

## 11. Висновок

Основними ризиками production MLOps-платформи є:

1. некоректний або шкідливий input;
2. перевантаження inference API;
3. несанкціонований Kubernetes access;
4. підміна model artifact;
5. небезпечний promotion моделі;
6. компрометація inference container;
7. відсутність traceability model lifecycle.

Реалізовані security controls зменшують ці ризики через validation, rate limiting, RBAC, checksum verification, audit logging, container hardening, NetworkPolicy та контрольований model promotion.
