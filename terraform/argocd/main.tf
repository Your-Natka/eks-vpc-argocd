resource "kubernetes_namespace" "infra_tools" {
  metadata {
    name = var.namespace
  }
}

resource "helm_release" "argocd" {
  name             = "argocd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  version          = "7.7.0" # Актуальна версія чарту
  namespace        = kubernetes_namespace.infra_tools.metadata[0].name
  create_namespace = false

  timeout = 900
  wait    = true

  values = [
    file("${path.module}/values/argocd-values.yaml")
  ]

  depends_on = [kubernetes_namespace.infra_tools]
}

resource "kubernetes_manifest" "argocd_applicationset" {
  depends_on = [helm_release.argocd]

  manifest = {
    apiVersion = "argoproj.io/v1alpha1"
    kind       = "ApplicationSet"
    metadata = {
      name      = "namespace-applications"
      namespace = kubernetes_namespace.infra_tools.metadata[0].name
    }
    spec = {
      generators = [
        {
          git = {
            repoURL  = var.gitops_repo_url
            revision = "HEAD"
            directories = [
              {
                path = "namespace/*"
              }
            ]
          }
        }
      ]
      template = {
        metadata = {
          name = "{{path.basename}}"
        }
        spec = {
          project = "default"
          source = {
            repoURL        = var.gitops_repo_url
            targetRevision = "HEAD"
            path           = "{{path}}"
          }
          destination = {
            server    = "https://kubernetes.default.svc"
            namespace = "{{path.basename}}"
          }
          syncPolicy = {
            automated = {
              prune    = true
              selfHeal = true
            }
            syncOptions = [
              "CreateNamespace=true"
            ]
          }
        }
      }
    }
  }
}
