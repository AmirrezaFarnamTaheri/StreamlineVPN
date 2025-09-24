# Deployment

This document describes how to deploy the StreamlineVPN application.

## Docker

### Build the Docker Image

You can build the Docker image from the source code using the provided Dockerfile.

```bash
docker build -t streamlinevpn/app:latest -f Dockerfile.production .
```

### Run with Docker

You can run the application in a Docker container.

```bash
docker run -d -p 8080:8080 --name streamline-vpn streamlinevpn/app:latest
```

### Use Pre-built Images from Docker Hub

You can use the pre-built Docker images from Docker Hub to run the application in a container.

```bash
docker run -d -p 8080:8080 --name streamline-vpn streamlinevpn/app:latest
```

## Kubernetes

### Manual Deployment

You can deploy the application to Kubernetes using the provided manifest files in the `kubernetes/` directory.

1.  **Apply the manifests:**

    ```bash
    kubectl apply -f kubernetes/
    ```

2.  **Verify the deployment:**

    ```bash
    kubectl get pods -n streamline-vpn
    ```

### Deploy with Helm

You can deploy the application to Kubernetes using the provided Helm chart in the `charts/` directory.

1.  **Install the chart:**

    ```bash
    helm install streamline-vpn charts/streamline-vpn
    ```

2.  **Verify the deployment:**

    ```bash
    helm list
    kubectl get pods
    ```
