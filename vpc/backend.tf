terraform {
  backend "s3" {
    bucket  = "mlops-tfstate-natala-2026"
    key     = "vpc/terraform.tfstate"
    region  = "eu-north-1"
    profile = "default"
  }
}