output "argocd_namespace" {
  description = "Argo CD namespace"
  value       = helm_release.argocd.namespace
}

output "argocd_release_name" {
  description = "Argo CD Helm release name"
  value       = helm_release.argocd.name
}

output "argocd_status" {
  description = "Argo CD Helm release status"
  value       = helm_release.argocd.status
}