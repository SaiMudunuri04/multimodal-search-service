# Kubernetes delivery

[`helm/multimodal-search-service/`](helm/multimodal-search-service/) is the **only** Helm chart and source of Kubernetes workload definitions in this repository. It contains Deployment, Service, ServiceAccount, ConfigMap, PodDisruptionBudget, HorizontalPodAutoscaler, and NetworkPolicy templates, plus release NOTES. [`argocd/application.yaml`](argocd/application.yaml) tracks the chart path in this repository; its header comment documents every placeholder and the GitOps flow.

Before deploying, review `values.yaml` for the image tag, artifact/data mounts, secrets, image pull access, resource sizing, health probes, and termination timing. `autoscaling.enabled` and `networkPolicy.enabled` are off by default; enable them only after the target cluster's metrics, ingress peers, DNS, and external inference egress are understood. The default NetworkPolicy peer allows pods in the same namespace only. A PDB with `minAvailable: 1` assumes at least two replicas.

Non-sensitive app configuration (the env vars the FastAPI app reads with `os.getenv`) lives in `values.yaml` under `appEnv` and is rendered into the `<release>-config` ConfigMap, which the Deployment consumes via `envFrom`. Keep secrets out of it: there is intentionally no committed `secret.yaml`; credentials must be created in the cluster or injected by a secret manager, then referenced with `envFromSecretName`.

Resource sizing targets CPU inference (the published image serves on CPU; training uses a separate GPU environment). Uncomment `nodeSelector`/`tolerations` in `values.yaml` only if you ship a GPU image variant.

## Manifest map

The rendered workload definitions live under [`helm/multimodal-search-service/templates/`](helm/multimodal-search-service/templates/): `deployment.yaml`, `service.yaml`, `serviceaccount.yaml`, `configmap.yaml`, `pdb.yaml`, `hpa.yaml`, and `networkpolicy.yaml`. `NOTES.txt` prints post-install usage hints. `helm/multimodal-search-service/values.yaml` supplies configuration for those templates, and `values.schema.json` validates its shape.

```sh
helm lint k8s/helm/multimodal-search-service --strict
helm template multimodal-search-service k8s/helm/multimodal-search-service --namespace multimodal-search-service
helm template multimodal-search-service k8s/helm/multimodal-search-service --namespace multimodal-search-service --set autoscaling.enabled=true --set networkPolicy.enabled=true
```

See [architecture](../docs/architecture.md) and the [operations runbook](../docs/operations.md). The chart is a reference release definition; this repository does not claim a live cluster deployment.
