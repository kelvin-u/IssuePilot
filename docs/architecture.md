# IssuePilot Architecture

## Goal

Convert a GitHub issue into a structured investigation run that can eventually produce:

- a root-cause report
- a candidate patch
- a verification summary
- a draft PR description

## Core Flow

1. User submits a GitHub issue URL.
2. Backend creates a run and normalizes the issue metadata.
3. Planner agent creates an investigation plan.
4. Investigator agent searches the repository and gathers evidence.
5. Sandbox runner reproduces the issue with tests or commands.
6. Fixer agent proposes a patch.
7. Verifier reruns tests and checks for improvement.
8. Frontend renders timeline, findings, and patch output.

## Verified-patch beta

Intake is submitted to a bounded in-process worker queue. Each run gets its own job directory, repository clone, selected runtime profile, and persisted artifacts. Inferred commands execute only in resource-limited, network-disabled Docker runners. The baseline must execute and fail before IssuePilot generates or applies a patch, and a run completes only when the same command passes afterward.

API-key access control, per-client rate limiting, cancellation, UUID-scoped retention cleanup, curated benchmark evaluation, and verified-run-only draft PR creation form the operational boundary around the pipeline.
