# IssuePilot

**An AI-powered GitHub agent that investigates repositories, proposes guarded code changes, and reports how to verify them.**

IssuePilot turns a public GitHub issue into a structured engineering investigation. Given an issue URL, it fetches the discussion, clones the repository into an isolated run workspace, searches for relevant code, selects a likely reproduction command, asks an AI fixer to generate a minimal patch, validates the diff, and presents the evidence for human review.

> **Current stage:** Verified-patch beta. Investigations run as cancellable background jobs, target commands execute in disposable containers, and a run completes only after a failing baseline becomes a passing post-patch check.

## Why I built it

Resolving an unfamiliar issue requires more than generating code. An engineer must identify the relevant context, form a hypothesis, reproduce the failure, make a focused change, and demonstrate that the change improves the result.

IssuePilot models that workflow as a traceable pipeline instead of treating the issue as a single prompt. Every run retains its workspace state, evidence, proposed diff, command output, and recommendation so a developer can review how the result was reached.

## How it works

```text
GitHub issue URL
       |
       v
Fetch issue, labels, and comments
       |
       v
Clone repository into a per-run workspace
       |
       v
Detect runtime and inspect relevant code
       |
       v
Plan a reproduction command
       |
       v
Generate and validate a unified diff
       |
       v
Apply patch in the run workspace
       |
       v
Require a passing post-patch verification and save the report
```

## Current capabilities

- Retrieves issue metadata and discussion comments from public GitHub issue URLs
- Creates an independent workspace and shallow repository clone for each run
- Detects Python, Node.js, or generic repository profiles
- Derives search terms and gathers candidate files, matching lines, and source snippets
- Selects a likely `pytest`, `npm test`, lint, or repository-survey command
- Uses the OpenAI Responses API to produce a structured diagnosis and unified diff
- Rejects oversized, binary, path-traversing, Git-metadata, and excessive-file patches
- Runs `git apply --check` before modifying the isolated clone
- Applies patches only after a containerized failing baseline and reruns the same command after the patch
- Persists run records and patch artifacts across API restarts
- Displays investigation timelines, evidence, patches, verification output, and run history
- Supports bounded background workers, cancellation, API-key auth, rate limits, and workspace retention
- Evaluates curated issues and can create a guarded GitHub draft PR from a verified run

## Safety decisions

Agent-generated patches are treated as untrusted input:

- Repository paths are normalized and checked before a patch is accepted.
- Patches cannot escape the cloned workspace or alter `.git` metadata.
- Binary patches and patches above configurable size/file limits are rejected.
- Every patch must pass `git apply --check` before application.
- Repository command execution is disabled by default and requires an explicit environment flag.
- Generated changes are applied only to the per-run clone, never to IssuePilot itself.

Enabled repository commands are invoked only through disposable Docker containers with networking disabled, capabilities dropped, CPU/memory/PID limits, and a no-new-privileges policy. Build the runner images before enabling execution; an unavailable runtime is treated as an infrastructure skip, never as a reproduced failure.

## Architecture

```text
apps/
|-- api/                     FastAPI service and investigation pipeline
|   `-- app/
|       |-- routes/          Intake, run history, and health endpoints
|       |-- schemas/         Pydantic API and report contracts
|       |-- services/        GitHub, workspace, agent, patch, and verification logic
|       `-- tools/           Repository listing, reading, and code search
`-- web/                     Next.js investigation dashboard
packages/
`-- shared-types/            Shared contract package scaffold
sandboxes/
|-- node-runner/             Node.js runner image
`-- python-runner/           Python runner image
docs/                        Architecture and delivery notes
```

| Method | Endpoint                | Purpose                                 |
| ------ | ----------------------- | --------------------------------------- |
| `GET`  | `/health`               | Service health check                    |
| `POST` | `/api/v1/issues/intake` | Queue an investigation and return its job |
| `GET`/`DELETE` | `/api/v1/jobs/{job_id}` | Poll or cancel a background investigation |
| `GET`  | `/api/v1/runs`          | List recent persisted runs              |
| `GET`  | `/api/v1/runs/{run_id}` | Retrieve one investigation report       |
| `POST` | `/api/v1/runs/{run_id}/draft-pr` | Create a guarded GitHub draft PR |

## Tech stack

- **Frontend:** Next.js, React, TypeScript
- **Backend:** FastAPI, Pydantic, Python 3.11+
- **AI:** OpenAI Responses API with structured output
- **Repository integration:** GitHub REST API and Git CLI
- **Execution:** Resource-limited disposable Python/Node Docker runners
- **Persistence:** JSON run records and artifacts in per-run workspaces

## Run locally

### Prerequisites

- Python 3.11+
- Node.js 22+
- Git
- An OpenAI API key for patch generation
- Optional: a GitHub token for higher API rate limits

### 1. Configure environment variables

Copy `.env.example` to `.env` and provide the credentials you want to use:

```env
OPENAI_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here
NEXT_PUBLIC_API_URL=http://localhost:8000
```

The app does not automatically load `.env` into a local shell. Export these values before starting the API, or configure them through your terminal or IDE.

### 2. Start the API

```bash
cd apps/api
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -e .
uvicorn app.main:app --reload --port 8000
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --port 8000
```

### 3. Start the web app

From the repository root:

```bash
npm install
npm run dev:web
```

Open [http://localhost:3000](http://localhost:3000). API documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs).

Before enabling repository execution, build the disposable runners from the repository root:

```bash
docker compose --profile runners build python-runner node-runner
```

### Important configuration

| Variable                              | Default     | Description                                          |
| ------------------------------------- | ----------- | ---------------------------------------------------- |
| `OPENAI_API_KEY`                      | unset       | Enables AI patch generation                          |
| `GITHUB_TOKEN`                        | unset       | Raises GitHub API rate limits                        |
| `ISSUEPILOT_WORKSPACE_ROOT`           | `data/runs` | Location for cloned repos and run artifacts          |
| `ISSUEPILOT_ENABLE_COMMAND_EXECUTION` | `false`     | Enables repository command execution                 |
| `ISSUEPILOT_ENABLE_PATCH_APPLICATION` | `true`      | Allows validated patches to be applied to run clones |
| `ISSUEPILOT_COMMAND_TIMEOUT_SECONDS`  | `45`        | Verification-command timeout                         |
| `ISSUEPILOT_MAX_PATCH_BYTES`          | `100000`    | Maximum accepted patch size                          |
| `ISSUEPILOT_MAX_PATCH_FILES`          | `8`         | Maximum files changed by one patch                   |
| `ISSUEPILOT_API_KEY`                  | unset       | If set, required in the `X-API-Key` request header   |
| `ISSUEPILOT_RATE_LIMIT_PER_MINUTE`    | `30`        | Per-client API request budget                        |
| `ISSUEPILOT_WORKSPACE_RETENTION_HOURS`| `168`       | Age after which UUID run workspaces are purged       |
| `ISSUEPILOT_MAX_BACKGROUND_WORKERS`   | `2`         | Concurrent investigation worker limit                |
| `ISSUEPILOT_ENABLE_DRAFT_PRS`         | `false`     | Enables explicit draft-PR requests for verified runs |

### Tests and benchmark

```bash
cd apps/api && pytest
npm run test:web
npm run build:web
npm run test:e2e
cd apps/api && python -m app.benchmark
```

The benchmark cases live in `benchmarks/issues.json`; each run writes a machine-readable report to `benchmarks/results/latest.json`. It performs real GitHub, model, Docker, and repository operations, so credentials and runner images are required.

## Roadmap

- [x] GitHub issue and comment ingestion
- [x] Per-run repository workspaces
- [x] Runtime detection and repository inspection
- [x] Structured AI patch generation
- [x] Guarded diff validation and application
- [x] Disk-backed investigation history
- [x] Investigation and patch-review dashboard
- [x] Execute all target code inside disposable Docker containers
- [x] Require a failing baseline and passing post-patch verification
- [x] Add backend, frontend, and end-to-end test suites
- [x] Move long-running investigations to a background job queue
- [x] Evaluate against a curated benchmark of real issues
- [x] Generate draft PR descriptions and guarded GitHub draft PRs
- [x] Add authentication, rate limiting, cancellation, and workspace retention policies

## Engineering focus

This project explores practical software-engineering problems beyond prompt construction:

- orchestrating a multi-stage agent workflow with explicit state transitions
- grounding model output in repository evidence
- validating and applying untrusted diffs safely
- managing ephemeral repository workspaces and persisted artifacts
- designing human-reviewable reports instead of opaque agent results
- separating investigation, patching, and verification concerns into testable services

## Project status

IssuePilot is under active development.

## License

This project is available under the [MIT License](LICENSE).
