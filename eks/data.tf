data "terraform_remote_state" "vpc" {
  backend = "s3"

  config = {
    bucket  = "mlops-tfstate-natala-2026"
    key     = "vpc/terraform.tfstate"
    region  = "eu-north-1"
    profile = "default"
  }
}