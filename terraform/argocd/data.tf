data "terraform_remote_state" "eks" {
  backend = "s3"

  config = {
    bucket  = "mlops-tfstate-natala-2026"
    key     = "eks/terraform.tfstate"
    region  = var.aws_region
    profile = var.aws_profile
  }
}

data "aws_eks_cluster" "this" {
  name = data.terraform_remote_state.eks.outputs.cluster_name
}

data "aws_eks_cluster_auth" "this" {
  name = data.terraform_remote_state.eks.outputs.cluster_name
}