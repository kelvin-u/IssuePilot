# IssuePilot

IssuePilot is a GitHub issue-to-patch agent for small open-source repositories.

The project is designed to look strong on a new grad software engineering resume:

- it takes a real GitHub issue URL
- plans an investigation
- searches relevant code and tests
- runs work inside a sandbox
- proposes a patch and verification report

This repository currently contains the first MVP scaffold:

- `apps/web`: Next.js frontend for issue intake and run inspection
- `apps/api`: FastAPI backend with run orchestration endpoints
- `sandboxes/`: Docker runners for Python and Node repositories
- `docs/`: architecture and roadmap notes

## Name

Product name: `IssuePilot`

Resume subtitle: `GitHub Issue-to-Patch Agent`

That framing is specific enough for recruiters to understand the problem immediately while still sounding like a polished product.

## MVP Scope

The first milestone supports:

- accepting a GitHub issue URL
- creating an investigation run
- fetching the real issue title, body, labels, and comment snapshot from GitHub
- preparing a per-run workspace with a repo clone attempt and sandbox runtime selection
- scanning the cloned repository for search hits, candidate files, and starter snippets
- planning a first repro command and optionally executing it behind an environment flag
- persisting runs to disk and showing lightweight investigation history
- tracking run state, hypothesis, evidence, and patch preview in the UI

Later milestones add:

- Docker-based test execution
- patch generation
- verification and draft PR output

## Monorepo Layout

```text
apps/
  api/      FastAPI backend
  web/      Next.js frontend
docs/       Architecture and delivery notes
packages/   Shared contracts and helpers
sandboxes/  Docker runners for target repos
```

## Quick Start

### 1. Backend

```bash
cd apps/api
python -m venv .venv
. .venv/Scripts/activate
pip install -e .
uvicorn app.main:app --reload --port 8000
```

Set `GITHUB_TOKEN` first if you want higher GitHub API rate limits for repeated testing.

### 2. Frontend

```bash
cd apps/web
npm install
npm run dev
```

### 3. Open the app

Visit `http://localhost:3000`

## Recommended Next Steps

1. Add a patch application and verification loop.
2. Evaluate against a small benchmark set of curated issues.
3. Draft pull request output for successful runs.
4. Replace heuristic issue planning with a model-driven planner agent.
5. Add authentication and guarded GitHub draft PR creation.
