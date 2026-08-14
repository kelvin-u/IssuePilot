"use client";

import { useEffect, useState } from "react";

import { IssueForm } from "../components/issue-form";
import { ReportCard } from "../components/report-card";
import { RunHistory } from "../components/run-history";
import { RunStatus } from "../components/run-status";
import { RunRecord, intakeIssue, listRuns } from "../lib/api";

export default function HomePage() {
  const [run, setRun] = useState<RunRecord | null>(null);
  const [runs, setRuns] = useState<RunRecord[]>([]);

  useEffect(() => {
    async function loadRuns() {
      try {
        const history = await listRuns();
        setRuns(history);
        if (history.length > 0) {
          setRun((current) => current ?? history[0]);
        }
      } catch {
        // Keep the landing experience usable even if history is unavailable.
      }
    }

    void loadRuns();
  }, []);

  async function handleIssueSubmit(issueUrl: string) {
    const nextRun = await intakeIssue(issueUrl);
    setRun(nextRun);
    setRuns((current) => [nextRun, ...current.filter((item) => item.id !== nextRun.id)]);
  }

  return (
    <main
      style={{
        minHeight: "100vh",
        padding: "3rem 1.25rem 5rem",
      }}
    >
      <div
        style={{
          maxWidth: "1100px",
          margin: "0 auto",
          display: "grid",
          gap: "1.5rem",
        }}
      >
        <section
          style={{
            display: "grid",
            gap: "0.75rem",
            padding: "2rem 0 0.5rem",
          }}
        >
          <span
            style={{
              width: "fit-content",
              padding: "0.35rem 0.7rem",
              borderRadius: "999px",
              border: "1px solid rgba(138, 69, 24, 0.22)",
              color: "var(--accent-dark)",
              background: "rgba(255, 250, 242, 0.75)",
              fontSize: "0.9rem",
            }}
          >
            GitHub Issue-to-Patch Agent
          </span>

          <div style={{ display: "grid", gap: "0.6rem", maxWidth: "780px" }}>
            <h1 style={{ margin: 0, fontSize: "clamp(2.8rem, 6vw, 5.2rem)" }}>
              IssuePilot
            </h1>
            <p style={{ margin: 0, fontSize: "1.1rem", color: "var(--muted)", lineHeight: 1.7 }}>
              Paste an issue. IssuePilot clones the repository, gathers code evidence,
              proposes a guarded patch, and verifies the result before it calls the fix complete.
            </p>
          </div>
        </section>

        <div className="workspace-grid">
          <div style={{ display: "grid", gap: "1.25rem" }}>
            <IssueForm onSubmit={handleIssueSubmit} />
            <RunHistory
              runs={runs}
              activeRunId={run?.id ?? null}
              onSelect={(selectedRun) => setRun(selectedRun)}
            />
          </div>
          <RunStatus run={run} />
        </div>

        <ReportCard run={run} />
      </div>
    </main>
  );
}
