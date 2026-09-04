terraform {
  backend "s3" {
    bucket  = "mlops-tfstate-natala-2026"
    key     = "argocd/terraform.tfstate"
    region  = "eu-north-1"
    profile = "NatkaMLOps"
  }
}