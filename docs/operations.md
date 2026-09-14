# Multimodal search operations

This is a deployment runbook for an operator to adapt. No AWS account or Kubernetes cluster has been connected by this repository.

## Before a rollout

1. Review the [architecture](architecture.md), tests, image tag, and [Helm values](../k8s/helm/multimodal-search-service/values.yaml).
2. Prepare `CATALOG_PATH`, `IMAGE_ROOT`, and optional `CLIP_MODEL`; mount inputs read-only and pre-cache approved model weights.
3. Provide image pull credentials if GHCR is private. Set resource limits to match measured model and traffic needs. Confirm the namespace's NetworkPolicy peers and egress before enabling it.
4. Render both chart modes locally: `helm lint k8s/helm/multimodal-search-service --strict`, `helm template multimodal-search-service k8s/helm/multimodal-search-service`, and `helm template multimodal-search-service k8s/helm/multimodal-search-service --set autoscaling.enabled=true --set networkPolicy.enabled=true`.

## Verify

- Check `kubectl -n multimodal-search-service rollout status deployment/multimodal-search-service` and inspect `/health/live` and `/health/ready` through the Service.
- Use the `X-Request-ID` response header to locate a matching JSON request log. Watch status and duration trends in the operator's logging system; no alert thresholds are prevalidated here.
- A readiness failure indicates local prerequisites such as model artifact, catalog, or document files. A liveness failure indicates an unhealthy process. Check the container's logs before restarting it.

## Recover

- If a new image is faulty, revert the Git commit or pin the previous reviewed image tag in the chart and let Argo CD sync it. Do not edit live resources as the lasting fix.
- If a model or data mount is missing, restore the read-only volume or secret and verify readiness before routing traffic.
- If HPA is enabled, confirm metrics-server availability and CPU requests. If NetworkPolicy is enabled, verify allowed ingress peers and any external inference/DNS egress.

## Known limits

The index is rebuilt per process and is not a persistent vector database. No proprietary image set, recall measure, or latency target is claimed.
