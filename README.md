# Homework №3 — Argo CD Deployment via Terraform

## Overview

This project demonstrates the deployment and configuration of **Argo CD** in an existing **AWS EKS cluster** using **Terraform** and the **Helm provider**.

The EKS cluster was created previously and is reused in this homework. The current project focuses on deploying Argo CD and configuring GitOps-based application delivery.

Argo CD is deployed into the `infra-tools` namespace and uses an **ApplicationSet** to automatically discover Kubernetes manifests from the GitOps repository.

### Technologies

- AWS EKS
- Terraform
- Helm
- Argo CD
- Kubernetes
- GitHub
- GitOps

---

## Architecture

```text
AWS EKS Cluster
│
├── infra-tools
│   └── Argo CD
│       └── ApplicationSet
│
└── application
    └── demo-nginx
```

### GitOps Flow

```text
GitHub Repository
       │
       │ namespace/*
       ▼
ApplicationSet
       │
       ▼
Argo CD Applications
       │
       ▼
Kubernetes
       │
       └── demo-nginx Deployment
```

---

## Repository Structure

The Terraform configuration for Argo CD is separated from the previously created EKS infrastructure.

```text
eks-vpc-argocd/
│
├── eks/
│   └── Existing EKS infrastructure
│
├── vpc/
│   └── Existing VPC infrastructure
│
├── terraform/
│   └── argocd/
│       ├── backend.tf
│       ├── data.tf
│       ├── main.tf
│       ├── outputs.tf
│       ├── provider.tf
│       ├── terraform.tf
│       ├── variables.tf
│       └── values/
│           └── argocd-values.yaml
│
├── screens/
│   ├── argocd-ui-applications.png
│   ├── gitops-repository.png
│   ├── terraform-argocd-localhost.png
│   └── project-tools-overview.png
│
├── .gitignore
└── README.md
```

The GitOps repository is maintained separately:

```text
goit-argo/
│
├── namespace/
│   ├── application/
│   │   ├── demo-nginx.yaml
│   │   └── ns.yaml
│   │
│   └── infra-tools/
│       └── ns.yaml
│
└── README.md
```

---

## Argo CD Deployment

Argo CD is deployed using the Terraform `helm_release` resource.

The official Argo Helm repository is used:

```text
https://argoproj.github.io/argo-helm
```

### Helm Release Configuration

| Parameter      | Value         |
| -------------- | ------------- |
| Release        | `argocd`      |
| Chart          | `argo-cd`     |
| Namespace      | `infra-tools` |
| Service type   | `ClusterIP`   |
| Server mode    | `--insecure`  |
| RBAC           | Enabled       |
| ApplicationSet | Enabled       |

All Helm values are stored separately in:

```text
terraform/argocd/values/argocd-values.yaml
```

The values file contains the required Argo CD configuration, including:

- `ClusterIP` service
- `--insecure` server argument
- RBAC configuration
- reconciliation timeout
- requeue timeouts
- resource requests and limits

---

## Terraform Deployment

Navigate to the Argo CD Terraform directory:

```bash
cd terraform/argocd
```

### Initialize Terraform

```bash
terraform init
```

### Validate Configuration

```bash
terraform validate
```

Expected result:

```text
Success! The configuration is valid.
```

### Create Execution Plan

```bash
terraform plan
```

### Apply Configuration

```bash
terraform apply
```

After successful deployment:

```text
Apply complete! Resources: 0 added, 2 changed, 0 destroyed.
```

Expected outputs:

```text
argocd_namespace = "infra-tools"
argocd_release_name = "argocd"
argocd_status = "deployed"
```

---

## Verify Argo CD

### Check Argo CD Pods

```bash
kubectl get pods -n infra-tools
```

All Argo CD components should have the status:

```text
Running
```

### Check ApplicationSet

```bash
kubectl get applicationset -n infra-tools
```

Expected:

```text
namespace-applications
```

### Check Argo CD Applications

```bash
kubectl get applications -n infra-tools
```

Expected result:

```text
NAME          SYNC STATUS   HEALTH STATUS
application   Synced        Healthy
infra-tools   Synced        Healthy
```

This confirms that Argo CD successfully discovered the directories from the GitOps repository and created the corresponding Applications.

---

## Argo CD UI

The Argo CD server is exposed locally using Kubernetes port-forwarding.

Run:

```bash
kubectl port-forward service/argocd-server -n infra-tools 8080:80
```

Open the following address in a browser:

```text
http://localhost:8080
```

### Login

Username:

```text
admin
```

The initial administrator password can be retrieved from the Kubernetes Secret:

```bash
kubectl -n infra-tools get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

The password is intentionally not stored in this repository.

---

## ApplicationSet

The Argo CD ApplicationSet uses a Git directory generator.

The generator monitors:

```text
namespace/*
```

Each directory under `namespace/` is automatically discovered and deployed as a separate Argo CD Application.

Current Applications:

```text
application
infra-tools
```

The `application` Application manages:

```text
namespace/application/
```

including the `demo-nginx` Deployment.

---

## GitOps Repository

The GitOps manifests are stored in a separate repository:

**goit-argo**

Repository:

https://github.com/Your-Natka/goit-argo

The repository contains the required structure:

```text
namespace/
├── application/
│   ├── demo-nginx.yaml
│   └── ns.yaml
│
└── infra-tools/
    └── ns.yaml
```

---

## Demo NGINX Application

The demo application is defined in:

```text
namespace/application/demo-nginx.yaml
```

The manifest creates an NGINX Deployment with two replicas.

### Verify Deployment

```bash
kubectl get deploy -n application
```

Expected result:

```text
NAME         READY   UP-TO-DATE   AVAILABLE
demo-nginx   2/2     2            2
```

### Verify Pods

```bash
kubectl get pods -n application
```

Both Pods should have the status:

```text
1/1   Running
```

---

## Access Demo NGINX

The NGINX application can be accessed locally using port-forwarding:

```bash
kubectl -n application port-forward deployment/demo-nginx 8081:80
```

Open:

```text
http://localhost:8081
```

The default NGINX welcome page should be displayed.

---

## GitOps Workflow

The complete GitOps workflow is:

```text
1. Modify Kubernetes manifests
          │
          ▼
2. Commit changes
          │
          ▼
3. Push changes to GitHub
          │
          ▼
4. ApplicationSet detects namespace/*
          │
          ▼
5. Argo CD creates or updates the Application
          │
          ▼
6. Argo CD synchronizes Kubernetes resources
          │
          ▼
7. Kubernetes runs the updated application
```

This demonstrates the GitOps deployment model, where Git acts as the source of truth for Kubernetes manifests.

---

## Verification Summary

The Homework №3 requirements have been successfully verified:

- [x] Argo CD deployed using Terraform `helm_release`
- [x] Argo CD deployed into the `infra-tools` namespace
- [x] Helm values stored in `argocd-values.yaml`
- [x] `ClusterIP` service configured
- [x] `--insecure` server mode configured
- [x] RBAC configured
- [x] Argo CD timeouts configured
- [x] ApplicationSet configured with `namespace/*`
- [x] GitOps repository contains the required namespace structure
- [x] `application` Application is `Synced` and `Healthy`
- [x] `infra-tools` Application is `Synced` and `Healthy`
- [x] `demo-nginx` Deployment created
- [x] Two NGINX Pods are running
- [x] Argo CD UI successfully verified
- [x] Demo NGINX application successfully verified

---

## Screenshots

The repository contains screenshots demonstrating the deployment and verification process:

- `argocd-ui-applications.png` — Argo CD UI with Applications
- `gitops-repository.png` — GitOps repository structure
- `terraform-argocd-localhost.png` — Terraform and local deployment process
- `project-tools-overview.png` — project tools and running infrastructure overview

---

## Result

The homework demonstrates a complete GitOps workflow:

**Terraform → Helm → Argo CD → ApplicationSet → GitHub → Kubernetes → NGINX**

Argo CD is successfully deployed to the existing EKS cluster, monitors the GitOps repository, automatically creates Applications from the `namespace/*` structure, and synchronizes Kubernetes resources.
