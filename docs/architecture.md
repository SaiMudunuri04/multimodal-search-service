# Multimodal search architecture

## Request and model path

Validated JSONL catalog and images → CLIP image/caption embeddings → normalized in-memory index → query embedding → ranked results

## Boundaries

- **Input:** Unique catalog IDs and image paths confined to `IMAGE_ROOT`. Image and text embedding dimensions must match.
- **Runtime:** `CATALOG_PATH`, `IMAGE_ROOT`, and optional `CLIP_MODEL` select the local catalog and approved model.
- **Failure behavior:** Missing catalog/images or incompatible embeddings make readiness return 503. Model loading may download weights unless pre-cached.

The FastAPI process exposes `/health/live` for process liveness and `/health/ready` for local prerequisites. Each HTTP response carries a generated `X-Request-ID`, `Cache-Control: no-store`, and `X-Content-Type-Options: nosniff`. JSON request logs record method, path, status, request ID, and duration, never request bodies, query strings, credentials, or user data. Logs are local process telemetry, not a claim of production monitoring.

The [single Helm chart](../k8s/helm/multimodal-search-service/) provides rolling updates, probes, resource bounds, security contexts, optional HPA and NetworkPolicy, and a PDB. [Argo CD](../k8s/argocd/application.yaml) points to that chart. Values need environment review before deployment, especially image pull access, ingress peers, external inference egress, and artifact mounts.

## Limits

The index is rebuilt per process and is not a persistent vector database. No proprietary image set, recall measure, or latency target is claimed.
