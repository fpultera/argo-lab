# Argo Rollouts Demo - argo-lab

Demo de **Argo Rollouts Canary Deployment** administrado por **ArgoCD** sobre Minikube.

---

## Requisitos

- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [minikube](https://minikube.sigs.k8s.io/docs/start/)
- [helm](https://helm.sh/) (opcional)
- [argocd CLI](https://argo-cd.readthedocs.io/en/stable/cli_installation/)

---

## 1. Levantar Minikube

```bash
minikube start --driver=docker --memory=4096 --cpus=2 --nodes=1 -p argo-lab
```

## 2. Instalar NGINX Ingress Controller

```bash
minikube addons enable ingress -p argo-lab
kubectl get pods -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

## 3. Instalar ArgoCD en Minikube

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### Verificar pods:

```bash
kubectl get pods -n argocd
```
### Exponer el server de ArgoCD (para desarrollo/local):

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

### Acceder en navegador: https://localhost:8080

### Usuario por defecto: admin

### Contraseña

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

## 4. Instalar Argo Rollouts

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

### Verificar pods

```bash
kubectl get pods -n argo-rollouts
```

### Instalar CLI local

```bash
# Linux
curl -sLO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts

# macOS
brew install argo-rollouts
```

## 5. Crear namespace para la demo

```bash
kubectl create namespace demo
```

## Clonar Repo

```bash
https://github.com/fpultera/argo-lab.git
```

## 6. Configurar ArgoCD Application

```bash
kubectl apply -f argo-app/nginx-demo-app.yaml -n argocd
```

```bash
Ingresar a la UI de argocd y ver que se alla sincronizado correctamente la app
Ahora los svc los vas a ver syncronizarce constantemente.
Para que ArgoCD no marque constantemente los Services nginx-canary y nginx-stable como OutOfSync (porque Argo Rollouts modifica dinámicamente los selector), hay que editar el ConfigMap argocd-cm e indicarle que ignore esas diferencias.
```

### 6a. Editar el ConfigMap

```bash
kubectl -n argocd edit configmap argocd-cm
```

Agregar la sección resource.customizations (si no existe, crearla):

```bash
data:
  resource.customizations: |
    Service:
      ignoreDifferences: |
        jsonPointers:
          - /spec/selector/rollouts-pod-template-hash
```

Esto le dice a ArgoCD que ignore los cambios en rollouts-pod-template-hash, que es lo que Rollouts actualiza dinámicamente.


### 6b. Reiniciar el pod del repo-server para que tome la nueva configuración

```bash
kubectl rollout restart deployment argocd-repo-server -n argocd
```

### 6c. Verificar

```bash
Hacé un resync en la app nginx-demo desde ArgoCD.
Ahora los Services deberían mantenerse en Synced aunque Rollouts cambie los selectors.
```

💡 Nota:

No es necesario desactivar el sync automático de la app.

Solo estás diciendo que ciertos campos específicos del Service pueden diferir del Git sin que ArgoCD los marque como OutOfSync.


Ahora con solo hacer un cambio en el spec del rollout.yaml cambiando al version de la imagen de nginx, y pusheando el cambio

deberias poder ver el cambio en rollout y en argocd, ademas de que si hacer varios F5 en al url vas a ver la diferencia

## 7. Dashboard de argo-rollout

0.0.0.0:3100