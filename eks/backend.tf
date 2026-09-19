terraform {
  backend "s3" {
    bucket  = "mlops-tfstate-natala-2026"
    key     = "eks/terraform.tfstate"
    region  = "eu-north-1"
    shared_credentials_files = ["~/.aws/credentials"]
  }
}