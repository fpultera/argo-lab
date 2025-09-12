# Crear namespace
kubectl create namespace argocd

# Instalar ArgoCD (manifiestos oficiales)
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Port forward para la UI de ArgoCD

kubectl port-forward svc/argocd-server -n argocd 8080:443