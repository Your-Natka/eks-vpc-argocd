# MLOps Homework №2 — VPC та EKS через Terraform

## Опис проєкту

Цей проєкт демонструє автоматизоване створення базової AWS-інфраструктури для майбутніх ML/MLOps-сервісів за допомогою **Terraform**.

У межах завдання створюються:

- AWS VPC;
- public та private subnets;
- NAT Gateway;
- Internet Gateway;
- Amazon EKS Kubernetes cluster;
- окремі CPU та workload node groups;
- workload isolation за допомогою Kubernetes labels та taints;
- зв'язок між VPC та EKS через `terraform_remote_state`;
- підключення до Kubernetes-кластера через `kubectl`.

Інфраструктура розділена на дві незалежні Terraform-конфігурації:

- `vpc/` — мережева інфраструктура;
- `eks/` — Kubernetes/EKS інфраструктура.

---

## Технології

- AWS
- Terraform
- Amazon VPC
- Amazon EKS
- Kubernetes
- kubectl
- Terraform Remote State
- Amazon S3 Backend

---

## Структура проєкту

````text
eks-vpc-cluster/
│
├── vpc/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── terraform.tf
│   └── backend.tf
│
├── eks/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── terraform.tf
│   ├── backend.tf
│   └── data.tf
│
└── README.md

---

# 1. AWS Authentication

Для роботи Terraform використовується AWS CLI profile:

```bash
NatkaMLOps
````

Перевірити налаштування профілю:

```bash
aws configure list --profile NatkaMLOps
```

Перевірити доступ до AWS:

```bash
aws sts get-caller-identity --profile NatkaMLOps
```

Очікуваний результат:

```json
{
  "UserId": "...",
  "Account": "...",
  "Arn": "arn:aws:iam::XXXXXXXXXXXX:user/NatkaMLOps"
}
```

AWS account використовується для навчального MLOps-середовища.

---

# 2. AWS Region

У цьому проєкті використовується AWS Region:

```text
eu-north-1
```

Це регіон Stockholm.

Перевірити регіон AWS CLI:

```bash
aws configure get region --profile NatkaMLOps
```

---

# 3. Terraform Backend

Terraform state зберігається в Amazon S3.

VPC та EKS мають окремі Terraform state.

Концептуальна структура:

S3 Terraform State Bucket
│
├── vpc/
│ └── terraform.tfstate
│
└── eks/
└── terraform.tfstate

Використання S3 backend дозволяє зберігати Terraform state централізовано та окремо для VPC і EKS.

---

# 4. VPC Configuration

Каталог:

```bash
cd vpc
```

VPC створюється за допомогою офіційного Terraform-модуля:

```text
terraform-aws-modules/vpc/aws
```

VPC містить:

- VPC CIDR;
- public subnets;
- private subnets;
- кілька Availability Zones;
- NAT Gateway;
- Internet Gateway;
- route tables;
- security groups;
- Terraform backend;
- Terraform outputs.

Private subnets використовуються для розміщення EKS worker nodes.

---

# 5. Initialize VPC

Перейти до каталогу VPC:

```bash
cd vpc
```

Ініціалізувати Terraform:

```bash
terraform init
```

Перевірити конфігурацію:

```bash
terraform validate
```

Переглянути план:

```bash
terraform plan
```

Якщо план коректний, створити VPC:

```bash
terraform apply
```

Підтвердити створення:

```text
yes
```

---

# 6. VPC Outputs

Після створення VPC можна перевірити Terraform outputs:

```bash
terraform output
```

Основні outputs:

```text
vpc_id
public_subnets
private_subnets
```

Окремо:

```bash
terraform output vpc_id
```

```bash
terraform output public_subnets
```

```bash
terraform output private_subnets
```

Ці значення використовуються EKS Terraform configuration.

---

# 7. Terraform Remote State

EKS не створює власну VPC.

Замість цього EKS отримує інформацію про вже створену VPC через:

```text
terraform_remote_state
```

містить configuration для отримання VPC Terraform state.

Концептуальна схема:

VPC Terraform State
│
│ terraform_remote_state
▼
EKS Terraform Configuration

Таким чином, VPC та EKS залишаються окремими Terraform-конфігураціями.

EKS отримує з VPC state:

vpc_id
private_subnets

---

# 8. EKS Configuration

Перейти до каталогу EKS:

```bash
cd ../eks
```

EKS створюється за допомогою офіційного Terraform-модуля:

```text
terraform-aws-modules/eks/aws
```

Назва Kubernetes-кластера:

mlops-eks

AWS Region:

eu-north-1

EKS використовує дані з VPC remote state:

vpc_id
private_subnets

Worker nodes розміщуються у private subnets.

---

# 9. Initialize EKS

Ініціалізувати Terraform:

```bash
terraform init
```

Перевірити конфігурацію:

```bash
terraform validate
```

Переглянути план:

```bash
terraform plan
```

Створити EKS:

```bash
terraform apply
```

Підтвердити:

```text
yes
```

Створення EKS та worker nodes може зайняти декілька хвилин.

---

# 10. Node Groups

У кластері створено дві окремі managed node groups для різних типів workloads.

## CPU Nodes

Node group:

```text
cpu-nodes
```

призначена для стандартних CPU workloads.

Для ноди встановлено label:

workload=cpu

Instance type:

t3.micro

Workload/GPU Nodes

Node group:

gpu-nodes

використовується як окрема workload node group для демонстрації ізоляції навантажень.

Для ноди встановлено label:

workload=gpu

Також застосовується Kubernetes taint:

workload=gpu:NoSchedule

Це означає, що звичайні Kubernetes workloads без відповідного toleration не будуть заплановані на цю node group.

Instance type:

t3.micro

---

# 11. EKS Cluster Verification

Перевірити список EKS-кластерів:

aws eks list-clusters \
 --region eu-north-1 \
 --profile NatkaMLOps

Очікується кластер:

mlops-eks

---

# 12. Configure kubectl

Після створення EKS-кластера потрібно налаштувати `kubectl`.

Використовується команда:

```bash
aws eks update-kubeconfig \
  --region eu-north-1 \
  --name mlops-eks \
  --profile NatkaMLOps
```

Перевірити поточний Kubernetes context:

kubectl config current-context

---

# 13. Check Kubernetes Cluster

Перевірити підключення до Kubernetes:

```bash
kubectl cluster-info
```

Перевірити worker nodes:

```bash
kubectl get nodes
```

Очікується, що worker nodes мають статус:

Ready

---

# 14. Check Node Groups

Список node groups:

```bash
aws eks list-nodegroups \
  --cluster-name mlops-eks \
  --region eu-north-1 \
  --profile NatkaMLOps
```

У кластері створено дві node groups:

```text
cpu-nodes
gpu-nodes
```

AWS автоматично додає унікальний суфікс до фактичної назви managed node group.

---

# 15. Check Kubernetes Resources

Перевірити всі nodes:

```bash
kubectl get nodes -o wide
```

Перевірити системні pods:

```bash
kubectl get pods -A
```

Перевірити namespaces:

```bash
kubectl get namespaces
```

Verified Kubernetes State

Після створення інфраструктури Kubernetes cluster був успішно перевірений.

Worker Nodes

Команда:

kubectl get nodes -o wide

показала дві worker nodes зі статусом:

STATUS
Ready
Ready

Обидві nodes успішно підключені до EKS-кластера.

Node Workloads

Для перевірки workload labels використано:

kubectl get nodes -L workload

Результат:

NAME STATUS WORKLOAD
ip-10-0-11-124.eu-north-1.compute.internal Ready gpu
ip-10-0-12-129.eu-north-1.compute.internal Ready cpu

Таким чином, Kubernetes nodes мають відповідні labels:

workload=gpu
workload=cpu
GPU Workload Isolation

Для GPU/workload node перевірено Kubernetes taint:

kubectl describe node ip-10-0-11-124.eu-north-1.compute.internal | grep -i taint

Результат:

Taints: workload=gpu:NoSchedule

Це підтверджує, що workload isolation через Kubernetes taint успішно налаштована.

Kubernetes System Pods

Команда:

kubectl get pods -A

показала, що основні системні компоненти працюють:

kube-system
├── aws-node Running
├── coredns Running
└── kube-proxy Running

AWS VPC CNI, CoreDNS та kube-proxy успішно працюють на worker nodes.

---

# 16. Terraform State Verification

Після успішного створення інфраструктури було виконано повторну перевірку Terraform state:

terraform plan

Результат:

No changes. Your infrastructure matches the configuration.

Terraform has compared your real infrastructure against your configuration
and found no differences, so no changes are needed.

Це підтверджує, що фактична AWS-інфраструктура відповідає поточній Terraform configuration.

# 17. Deployment Order

Інфраструктура створюється в такому порядку:

```text
1. AWS Authentication
        ↓
2. Terraform VPC
        ↓
3. VPC Outputs
        ↓
4. terraform_remote_state
        ↓
5. Terraform EKS
        ↓
6. EKS Node Groups
        ↓
7. aws eks update-kubeconfig
        ↓
8. kubectl get nodes
```

Спочатку потрібно створити VPC:

```bash
cd vpc

terraform init
terraform validate
terraform plan
terraform apply
```

Після цього створюється EKS:

```bash
cd ../eks

terraform init
terraform validate
terraform plan
terraform apply
```

Після успішного створення EKS налаштовується Kubernetes context:

aws eks update-kubeconfig \
 --region eu-north-1 \
 --name mlops-eks \
 --profile NatkaMLOps

Після цього перевіряється стан worker nodes:

kubectl get nodes

---

# 18. Destroy Infrastructure

Після завершення перевірки AWS-ресурси потрібно видалити, щоб уникнути зайвих витрат.

## Delete EKS

Спочатку:

```bash
cd eks
```

Виконати:

```bash
terraform destroy
```

Підтвердити:

```text
yes
```

## Delete VPC

Після успішного видалення EKS:

```bash
cd ../vpc
```

Виконати:

```bash
terraform destroy
```

Підтвердити:

```text
yes
```

Порядок видалення:

```text
EKS
 ↓
Node Groups
 ↓
VPC
 ↓
Subnets
 ↓
NAT Gateway
 ↓
Internet Gateway
```

EKS необхідно видаляти **перед VPC**, оскільки кластер використовує мережеву інфраструктуру VPC.

---

# 19. Useful Commands

## AWS identity

```bash
aws sts get-caller-identity --profile NatkaMLOps
```

## AWS region

```bash
aws configure get region --profile NatkaMLOps
```

## List EKS clusters

```bash
aws eks list-clusters \
  --region eu-north-1 \
  --profile NatkaMLOps
```

## Update kubeconfig

```bash
aws eks update-kubeconfig \
  --region eu-north-1 \
  --name <cluster-name> \
  --profile NatkaMLOps
```

## Kubernetes cluster info

```bash
kubectl cluster-info
```

## Kubernetes nodes

```bash
kubectl get nodes
```

## Kubernetes nodes with details

```bash
kubectl get nodes -o wide
```

## Kubernetes nodes with workload labels

```bash
kubectl get nodes -L workload
```

## Kubernetes pods

```bash
kubectl get pods -A
```

## Kubernetes namespaces

```bash
kubectl get namespaces
```

## EKS node groups

```bash
aws eks list-nodegroups \
  --cluster-name mlops-eks \
  --region eu-north-1 \
  --profile NatkaMLOps
```

## Terraform validation

```bash
terraform validate
```

## Terraform plan

```bash
terraform plan
```

---

# 20. Acceptance Criteria

20. Acceptance Criteria

Проєкт відповідає вимогам домашнього завдання:

- Використовується Terraform.
- Використовується terraform-aws-modules/vpc/aws.
- Використовується terraform-aws-modules/eks/aws.
- Є окремий каталог vpc/.
- Є окремий каталог eks/.
- VPC має public subnets.
- VPC має private subnets.
- Використовується кілька Availability Zones.
- Налаштований NAT Gateway.
- Налаштований Internet Gateway.
- VPC експортує vpc_id.
- VPC експортує public_subnets.
- VPC експортує private_subnets.
- EKS використовує terraform_remote_state.
- EKS отримує VPC information через Terraform outputs.
- Створюється CPU node group.
- Створюється окрема workload/GPU node group.
- CPU node має label workload=cpu.
- Workload/GPU node має label workload=gpu.
- Workload/GPU node має taint workload=gpu:NoSchedule.
- terraform init працює для VPC.
- terraform validate працює для VPC.
- terraform apply працює для VPC.
- terraform init працює для EKS.
- terraform validate працює для EKS.
- terraform apply працює для EKS.
- terraform plan після створення повертає No changes.
- Працює aws eks update-kubeconfig.
- Працює kubectl cluster-info.
- Працює kubectl get nodes.
- Worker nodes мають статус Ready.
- VPC CNI (aws-node) працює.
- CoreDNS працює.
- kube-proxy працює.
- Після перевірки ресурси можуть бути видалені через terraform destroy.

---

# 21. Conclusion

У результаті було створено базову AWS-інфраструктуру для MLOps-середовища за допомогою Terraform.

Проєкт демонструє:

- Infrastructure as Code;
- модульний підхід Terraform;
- окреме керування VPC та EKS;
- Terraform Remote State;
- передачу outputs між Terraform-конфігураціями;
- використання Amazon VPC;
- використання Amazon EKS;
- Kubernetes cluster management;
- створення managed node groups;
- workload за допомогою Kubernetes labels та taints;
- роботу з AWS CLI;
- підключення до EKS через kubectl;
- перевірку відповідності Terraform state фактичній інфраструктурі.

Фактична інфраструктура успішно перевірена:

VPC
↓
EKS cluster: mlops-eks
↓
CPU node group
↓
Workload/GPU node group
↓
2 Kubernetes nodes
↓
STATUS = Ready

Workload isolation:

CPU node
└── workload=cpu

GPU/workload node
├── workload=gpu
└── workload=gpu:NoSchedule

Порядок створення:

VPC → EKS → Node Groups → kubectl

Порядок видалення:

EKS → VPC

Таким чином, Terraform configuration успішно створює, перевіряє та дозволяє керувати базовою AWS-інфраструктурою для майбутніх MLOps workloads.
