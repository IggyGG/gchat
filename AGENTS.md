# GChat agent entry point

Read the existing [PLAN.md](PLAN.md), [TESTPLAN.md](TESTPLAN.md), and the
[release workflow](docs/AUTOMATIC_RELEASES.md) before meaningful work. Record
task owner, scope, source/checkout, decisions, checks, remaining work and UTC
updates in the existing plan. Keep source publication, qualified images,
deployment and actual runtime acceptance distinct.

Follow the shared [documentation routine](https://forgejo.triform.dev/ghost-local/research/src/branch/main/docs/pipeline/AGENT-WORKFLOW.md)
and [cloud operating agreement](https://forgejo.triform.dev/triform/tf-infra/src/branch/main/docs/runbooks/cloud-operations.md).
Use a contained task checkout; preserve another owner's active edits, release
requests, clocks, original failures and rollback evidence. Publish coherent
checkpoints through the repository's existing Forgejo main/source-mirror route.
Run affected source checks and the release workflow's actual-image/native gates
before runtime activation. A documentation checkpoint is not release acceptance.

Public GitHub reads and Git access use the shared GitHub service. Never print
credentials or put them in receipts. Existing private Forgejo publication keeps
its configured route.

The shared storage programme is CLOUD-OPS-1 in PLAN.md, linked to the canonical
infrastructure execution record. Storage eligibility belongs to the producer;
age alone, a healthy cleanup Job, or a missing Pod reference is not deletion
proof. Keep current releases, active work, rollback paths and native restore
verification intact.
