# Deployment Guide

ai‑code‑review‑squad can be deployed locally with docker‑compose or to Kubernetes using the provided Helm chart.  This document outlines the steps for both scenarios and describes configuration options.

## Local Development

1. Ensure Docker and Docker Compose are installed.
2. Copy `.env.example` to `.env` and adjust variables if necessary.  For local development, no GitHub credentials are required – Mock LLM mode is enabled by default.
3. Run `make up`.  This invokes `docker-compose up --build`, applies database migrations and seeds demo data.  The backend runs on http://localhost:8000 and the frontend on http://localhost:5173.
4. To stop the services, run `make down`.

## Kubernetes Deployment

### Helm Installation

The `k8s/helm/ai-code-review-squad` chart defines deployments for the API, workers, frontend, PostgreSQL and Redis.  Prerequisites:

* A Kubernetes cluster (EKS, GKE, AKS, etc.) with ingress and cert manager installed.
* Helm 3 installed locally.
* A container registry where built images can be pushed.

Deploy the chart:

```bash
helm upgrade --install ai-code-review-squad k8s/helm/ai-code-review-squad \
  --namespace ai-review --create-namespace \
  -f k8s/overlays/prod/values.yaml
```

This command installs the chart with production values.  For development, use the `dev/values.yaml` overlay.

### Configuration

Key values configurable in `values.yaml` include:

| Name                    | Description                                                            |
|-------------------------|------------------------------------------------------------------------|
| `image.repository`      | Container image repository for the backend                             |
| `image.tag`             | Image tag (usually set by CI)                                          |
| `frontend.image`        | Container image for the frontend                                       |
| `resources`             | CPU and memory requests/limits for each component                     |
| `env`                   | Environment variables passed to the backend and workers               |
| `ingress.enabled`       | Enable or disable ingress resources                                    |
| `autoscaling`           | Configure HPA or KEDA (based on CPU or queue depth)                    |

Secrets such as database passwords and GitHub app credentials should be provided via Helm values using Kubernetes Secret objects.  See `k8s/helm/ai-code-review-squad/templates/secret.yaml` for examples.

### Terraform

An optional Terraform module is provided in `infra/terraform` for bootstrapping cloud infrastructure (VPC, Kubernetes cluster, managed PostgreSQL and Redis).  The module is intentionally minimal and uses placeholder variables.  Refer to `infra/terraform/README.md` for details.

## Release Process

CI builds and pushes images to the registry and uses semantic‑release to create tags and release notes.  The Helm chart values reference the image tag via `.Chart.AppVersion`.  To deploy a new version:

1. Merge your changes into `main`.  GitHub Actions will run tests and publish a release tag.
2. Pull the latest chart values and update your cluster via `helm upgrade`.  Blue/green or canary releases can be achieved by changing the `image.tag` or adjusting HPA weights in separate Helm releases.

Refer to the runbooks for troubleshooting deployment issues.