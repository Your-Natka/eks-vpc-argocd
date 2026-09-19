module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = var.cluster_name
  kubernetes_version = var.kubernetes_version

  endpoint_public_access = true

  cloudwatch_log_group_retention_in_days = 7

  vpc_id     = data.terraform_remote_state.vpc.outputs.vpc_id
  subnet_ids = data.terraform_remote_state.vpc.outputs.private_subnets

  enable_irsa = true

  create_kms_key = false

  encryption_config = {
    provider_key_arn = "arn:aws:kms:eu-north-1:650830975789:key/5e0fd76e-016a-4c2f-9659-d0fcbf5a2aa4"
    resources        = ["secrets"]
  }

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

    cpu-small = {
      name = "cpu-small"

      instance_types = ["t3.small"]

      min_size     = 1
      max_size     = 2
      desired_size = 2

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

