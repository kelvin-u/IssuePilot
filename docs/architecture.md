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

## Initial MVP Cut

The current scaffold now covers real GitHub issue ingestion, per-run workspace preparation, repository inspection, repro-command planning, and disk-backed run history. Each run gets its own job directory, a repository clone attempt, a selected sandbox runtime profile, and persisted investigation artifacts.

The next meaningful milestone is moving from planned execution into verified patch generation so the agent can prove that a code change actually improves the reported failure.
