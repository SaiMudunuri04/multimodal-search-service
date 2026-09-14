# Multimodal search

[Architecture](docs/architecture.md) · [Operations runbook](docs/operations.md) · [Helm chart](k8s/helm/multimodal-search-service/) · [Argo CD application](k8s/argocd/application.yaml)

An independent service for CLIP-based image and text retrieval. This repository contains executable source, tests,
a container, Helm release, Argo CD application, and a CI workflow that builds an
immutable GHCR image after tests pass. It is a reference implementation; it has not
been deployed to a user's AWS account or Kubernetes cluster.

## Run

```sh
python -m pip install -e '.[test]'
python -m pytest -q
ruff check .
helm lint k8s/helm/multimodal-search-service --strict
uvicorn service.app:app --reload
```

`/health/live` checks the process. `/health/ready` checks required local resources. Responses include a request ID and no-store/nosniff headers; JSON request logs omit bodies and query strings.
Configure data, model artifacts, and inference endpoints before serving traffic.

## Delivery

The workflow tests pull requests, then builds/pushes an image to GHCR on `main` and
updates the Helm image tag to the tested commit. Argo CD follows the single chart at [`k8s/helm/multimodal-search-service/`](k8s/helm/multimodal-search-service/).
Install `k8s/argocd/application.yaml` in a cluster with Argo CD, set environment-specific
Helm values, provide secrets through a cluster secret manager, and make the package
pullable by the cluster. Model/data volumes are configured through `volumes` and
`volumeMounts`; use `envFromSecretName` for credentials. The workflow does not
provision AWS or a cluster.

`.env.example` contains placeholders only. Never commit credentials or private data.

## Build and serve

Provide a JSONL catalog with unique `id`, `image_path`, and optional `caption` fields; image paths must stay beneath `IMAGE_ROOT`. On readiness, the service loads CLIP, embeds images and captions, and builds an in-memory catalog. Model weights are downloaded from the configured model hub unless pre-cached.

```sh
CATALOG_PATH=/path/catalog.jsonl IMAGE_ROOT=/path/images uvicorn service.app:app --host 127.0.0.1
```

Mount the catalog and images read-only. Provide an approved model cache and enough memory for the catalog. For a large production catalog, replace the in-memory index with a persistent vector store and add recall/latency evaluation. No proprietary images or retrieval metrics are claimed.
