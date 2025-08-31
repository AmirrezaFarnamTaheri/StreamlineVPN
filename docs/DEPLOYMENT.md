Deployment
==========

Kubernetes
----------

- See manifests under `k8s/`
- Configure secrets, PVs, and HPA as needed

Docker
------

`docker build -t submerger:latest -f Dockerfile .`

`docker run --rm -p 8001:8001 submerger:latest`

