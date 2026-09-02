module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = var.cluster_name
  kubernetes_version = var.kubernetes_version

  endpoint_public_access = true

  vpc_id     = data.terraform_remote_state.vpc.outputs.vpc_id
  subnet_ids = data.terraform_remote_state.vpc.outputs.private_subnets

  enable_irsa = true

  addons = {
    coredns = {
      most_recent    = true
      before_compute = true
    }

    kube-proxy = {
      most_recent    = true
      before_compute = true
    }

    vpc-cni = {
      most_recent    = true
      before_compute = true
    }
  }

  eks_managed_node_groups = {
    cpu-nodes = {
      name = "cpu-nodes"

      instance_types = ["t3.micro"]

      min_size     = 1
      max_size     = 1
      desired_size = 1

      labels = {
        workload = "cpu"
      }
    }

    gpu-nodes = {
      name = "gpu-nodes"

      instance_types = ["t3.micro"]

      min_size     = 1
      max_size     = 1
      desired_size = 1

      labels = {
        workload = "gpu"
      }

      taints = {
        gpu = {
          key    = "workload"
          value  = "gpu"
          effect = "NO_SCHEDULE"
        }
      }
    }
  }

  tags = {
    Project     = "MLOps"
    Environment = "dev"
    ManagedBy   = "Terraform"
  }
}

