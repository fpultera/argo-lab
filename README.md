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

kubectl argo rollouts dashboard

### Aclaraciones

# ArgoCD y Argo Rollouts: Quién hace qué

Este documento explica las responsabilidades de ArgoCD y Argo Rollouts en un despliegue canary.

## 🔹 1. Qué hace ArgoCD

> ArgoCD es tu controlador GitOps.

Lo que hace con tu `Application` **nginx-demo**:

* **Observa el repositorio Git**: `https://github.com/fpultera/argo-lab.git` en el `path` `demo-app`.
* **Compara los manifiestos declarativos** (`Rollout`, `Services`, `Ingress`) con el estado actual del clúster.
* **Aplica los cambios automáticamente** porque la `Application` tiene la siguiente política de sincronización:
    ```yaml
    syncPolicy:
      automated:
        prune: true
        selfHeal: true
    ```
    * `prune: true`: Elimina recursos del clúster que ya no existen en Git.
    * `selfHeal: true`: Corrige desviaciones ("drifts") si un recurso es modificado manualmente en el clúster, restaurándolo al estado definido en Git.

**Importante**: ArgoCD solo aplica la versión declarativa que está en Git. No entiende la lógica del canary ni el enrutamiento de tráfico progresivo que gestiona Argo Rollouts.

---

## 🔹 2. Qué hace Argo Rollouts

> Argo Rollouts es tu controlador de despliegue avanzado.

Lo que hace con tu `Rollout` **nginx**:

* **Administra el despliegue canary**: Cambia progresivamente la cantidad de tráfico entre las versiones `nginx-stable` y `nginx-canary`.
* **Modifica dinámicamente** los `selectors` de los `Services` y las reglas del `Ingress` para enrutar el tráfico según los pesos definidos en la estrategia.
* **Sigue los pasos** definidos en `spec.strategy.canary.steps`:
    1.  Enruta el 20% del tráfico a la nueva versión y pausa.
    2.  Aumenta al 50% del tráfico y vuelve a pausar.
    3.  Completa el despliegue al 100%.

**Importante**: Rollouts modifica los recursos dinámicamente en el clúster, pero **no altera** la definición declarativa en Git. Por esta razón, ArgoCD podría marcar los `Services` como `OutOfSync` si no configuramos `ignoreDifferences` para los campos que Rollouts gestiona.

---

## 🔹 3. Quién controla qué

| Componente      | Qué controla                                                                                                                                                              |
| :-------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **ArgoCD** | Sincroniza **todo** desde Git: `Rollout`, `Services`, `Ingress`. Aplica los cambios declarativos. No tiene conocimiento del proceso canary.                                   |
| **Argo Rollouts** | Controla el **proceso de despliegue canary**: mueve el tráfico, modifica los `selectors` de los `Services` y actualiza el `Ingress`.                                         |
| **Usuario / Git** | Inicia el flujo cambiando la versión de la imagen (`image`) o cualquier otro manifiesto YAML en Git. Esto dispara a `ArgoCD`, que a su vez activa a `Argo Rollouts` para ejecutar el canary. |

---

## 🔹 Ejemplo de flujo completo

1.  **Cambias la `image`** en el archivo `rollout.yaml` y ejecutas `git push`.
2.  **ArgoCD** detecta el cambio en Git y aplica la nueva versión del `Rollout` en el clúster.
3.  **Argo Rollouts** toma el control y comienza a mover el tráfico de manera progresiva, siguiendo los `steps` de la estrategia canary.
4.  Durante el proceso, los `Services` `nginx-stable` y `nginx-canary` cambian sus `selectors` dinámicamente.
5.  Gracias a la configuración `ignoreDifferences`, **ArgoCD** no entra en conflicto con los cambios dinámicos que realiza Argo Rollouts y mantiene el estado de la aplicación como `Synced`.