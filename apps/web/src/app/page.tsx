"use client";

import { useEffect, useState } from "react";

import { IssueForm } from "../components/issue-form";
import { InvestigationLoading, ProcessOverview } from "../components/investigation-loading";
import { ReportCard } from "../components/report-card";
import { RunHistory } from "../components/run-history";
import { RunStatus } from "../components/run-status";
import { type JobProgress, type RunRecord, intakeIssue, listRuns } from "../lib/api";

export default function HomePage() {
  const [run, setRun] = useState<RunRecord | null>(null);
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [submittedIssueUrl, setSubmittedIssueUrl] = useState("");
  const [jobProgress, setJobProgress] = useState<JobProgress>({
    status: "queued",
    stage: "queued",
    stage_detail: "Waiting for an investigation worker.",
  });

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
    setSubmittedIssueUrl(issueUrl);
    setJobProgress({ status: "queued", stage: "queued", stage_detail: "Waiting for an investigation worker." });
    setIsInvestigating(true);
    try {
      const nextRun = await intakeIssue(issueUrl, setJobProgress);
      setRun(nextRun);
      setRuns((current) => [nextRun, ...current.filter((item) => item.id !== nextRun.id)]);
    } finally {
      setIsInvestigating(false);
    }
  }

  return (
    <main className="app-shell">
      <div className="app-container">
        <section className="hero">
          <div>
            <p className="eyebrow">IssuePilot</p>
            <h1>Investigate a GitHub issue</h1>
            <p>Trace a reported bug through its repository, generate a focused patch, and verify the result in an isolated environment.</p>
          </div>
        </section>

        <IssueForm onSubmit={handleIssueSubmit} />

        {isInvestigating ? (
          <InvestigationLoading
            issueUrl={submittedIssueUrl}
            stage={jobProgress.stage}
            stageDetail={jobProgress.stage_detail}
          />
        ) : (
          <>
            <ProcessOverview />
            <div className="workspace-grid">
              <RunStatus run={run} />
              <RunHistory
                runs={runs}
                activeRunId={run?.id ?? null}
                onSelect={(selectedRun) => setRun(selectedRun)}
              />
            </div>
            <ReportCard run={run} />
          </>
        )}
      </div>
    </main>
  );
}
