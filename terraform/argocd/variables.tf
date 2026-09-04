variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-north-1"
}

variable "aws_profile" {
  description = "AWS CLI profile"
  type        = string
  default     = "NatkaMLOps"
}

variable "cluster_name" {
  description = "Existing EKS cluster name"
  type        = string
  default     = "mlops-eks"
}

variable "gitops_repo_url" {
  description = "GitOps repository URL"
  type        = string
  default     = "https://github.com/Your-Natka/goit-argo.git"
}

variable "namespace" {
  description = "Kubernetes namespace for Argo CD"
  type        = string
  default     = "infra-tools"
}