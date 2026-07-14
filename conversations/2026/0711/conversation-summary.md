# Argo Events & Argo Workflows — English Summary

## Topics We Covered

### Argo Workflows vs. Argo Events

- **Argo Workflows** is responsible for executing workflows.
- **Argo Events** detects external events (such as webhooks, Kafka messages, or schedules) and triggers workflows.
- Typical event flow:

```text
External System
      ↓
 EventSource
      ↓
   EventBus
      ↓
    Sensor
      ↓
WorkflowTemplate
      ↓
   Workflow
```

### Namespace Design

We separated responsibilities into two namespaces.

| Namespace | Purpose |
|-----------|---------|
| `argo-events` | EventBus, EventSource, Sensor |
| `argo` | Workflow, WorkflowTemplate |

Benefits:

- Clear separation of responsibilities
- Easier RBAC management
- Closer to production-style deployments

### RBAC Between Namespaces

Because the Sensor runs in `argo-events` but creates Workflows in `argo`, additional RBAC permissions are required.

The Sensor's ServiceAccount needs permission to:

- Create Workflows
- Create WorkflowTemplates (if required)

Without these permissions:

- Events are received successfully.
- Sensors are triggered successfully.
- Workflow creation fails due to RBAC errors.

### WorkflowTemplate

Instead of embedding a complete Workflow inside the Sensor, we created a reusable `WorkflowTemplate`.

Advantages:

- Reusable
- Easier to maintain
- Cleaner Sensor manifests
- Better suited for Helm templating

### Installing Argo Events

We installed:

- `install.yaml`
- `install-validating-webhook.yaml`

The validating webhook performs server-side validation before Event resources are accepted by Kubernetes.

### Helm

Useful commands:

```bash
helm lint ./kubernetes

helm template ./kubernetes \
  --values ./kubernetes/values.yaml
```

`helm lint`

- Validates Helm chart syntax
- Detects template issues

`helm template`

- Renders the final Kubernetes manifests
- Useful for debugging generated YAML

### Helm vs. Argo Template Syntax

Both Helm and Argo use `{{ ... }}`.

Since Helm renders templates first, Argo expressions must be escaped when using Helm.

### Webhook Event Flow

```text
curl
  ↓
Webhook EventSource
  ↓
EventBus
  ↓
Sensor
  ↓
WorkflowTemplate
  ↓
Workflow
```

### Moving from Webhook to Kafka

Next topics include:

- Kafka EventSource
- Topics
- Brokers
- Docker Compose
- Local testing with Kind

### Future Learning Roadmap

- Kafka EventSource
- Event filtering
- Sensor dependencies
- DAG Workflows
- Workflow-of-Workflows
- CronWorkflows
- Helm best practices
- Production RBAC
- Retry strategies
- Artifact storage (MinIO/S3)

---

## Key Questions I Asked

- Why is `install-validating-webhook.yaml` necessary?
- Why separate `argo-events` and `argo` namespaces?
- Why does the Sensor require additional RBAC?
- What is the difference between `helm lint` and `helm template`?
- How does Helm conflict with Argo's `{{ }}` syntax?
- How does Argo Events map a Webhook event to a Workflow?
- What should I learn next after Webhook events?

---

## Architecture Diagram

```text
External System
      │
      ▼
 EventSource
      │
      ▼
   EventBus
      │
      ▼
    Sensor
      │
      ▼
WorkflowTemplate
      │
      ▼
   Workflow
```

---

## What This Discussion Demonstrates

- The roles of Argo Workflows and Argo Events
- Why WorkflowTemplates improve maintainability
- Why cross-namespace Sensors require RBAC
- The purpose of the validating webhook
- The difference between `helm lint` and `helm template`
- How Helm and Argo template syntax interact
- A typical webhook-driven event flow

---

## Best Practices

- Keep Argo Events and Workflows in separate namespaces.
- Reuse WorkflowTemplates instead of embedding Workflows.
- Validate Helm charts with `helm lint`.
- Inspect rendered manifests using `helm template`.
- Design Sensors with the minimum RBAC permissions required.

---

## Common Pitfalls

- Forgetting RBAC permissions for cross-namespace Workflow creation.
- Confusing `helm lint` with `helm template`.
- Forgetting to escape Argo template expressions inside Helm templates.
- Embedding large Workflows directly inside Sensor manifests.

---

## Specific Feedback On My English

Instead of:

> How do I not define this?

Use:

- Do I need to define this?
- Is this required?

Instead of:

> It doesn't make any sense.

Use:

- I'm not following this part.
- Could you clarify that?
- I'm not sure I understand why that's necessary.

Instead of:

> Is this enough?

Use:

- Would this configuration be sufficient?
- Would this approach work in production?
- Is there anything I'm missing?

---

## Technical Clarity Feedback

The discussion became much clearer after distinguishing:

- Argo Events (event detection)
- Argo Workflows (workflow execution)
- Sensors (trigger logic)
- WorkflowTemplates (reusable workflow definitions)

Keeping these responsibilities separate makes the overall architecture easier to understand.

---

## Example Questions Or Phrases For Future Use

- Could you walk me through the event flow?
- Which component is responsible for creating the Workflow?
- Why is this RBAC permission required?
- Is this considered a best practice?
- How would this work in production?
- Does the Sensor retry automatically?
- What are the trade-offs between embedding a Workflow and referencing a WorkflowTemplate?

---

## Suggested Next Topic

- Kafka EventSource
- Event filtering
- Sensor dependencies
- DAG Workflows
- Workflow-of-Workflows
- CronWorkflows
- Retry strategies
- Synchronization and mutexes
- Artifact storage (MinIO/S3)
- Production architecture for Argo Events and Argo Workflows