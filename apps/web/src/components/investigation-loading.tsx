"use client";

const stages = [
  { id: "reading_issue", title: "Read the issue", detail: "Collecting the description, labels, and discussion." },
  { id: "preparing_workspace", title: "Prepare a workspace", detail: "Cloning the repository into an isolated run directory." },
  { id: "inspecting_repository", title: "Find the relevant code", detail: "Searching for likely files, symbols, and failure paths." },
  { id: "running_baseline", title: "Reproduce the problem", detail: "Running a safe baseline check inside Docker." },
  { id: "generating_patch", title: "Build a focused patch", detail: "Generating and validating the smallest credible change." },
  { id: "verifying_patch", title: "Verify the result", detail: "Rerunning the same check before calling the fix complete." },
];

export function InvestigationLoading({
  issueUrl,
  stage,
  stageDetail,
}: {
  issueUrl: string;
  stage: string;
  stageDetail: string;
}) {
  const activeIndex = Math.max(0, stages.findIndex((item) => item.id === stage));

  return (
    <section className="loading-card" aria-live="polite" aria-busy="true">
      <div className="loading-card__header">
        <div className="loader-mark" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <div>
          <p className="eyebrow">Investigation running</p>
          <h2>Investigating issue</h2>
          <p className="loading-summary">
            {stageDetail || "Starting the investigation."} <span>This can take a few minutes.</span>
          </p>
          <p className="loading-url">{issueUrl}</p>
        </div>
      </div>

      <ol className="loading-steps">
        {stages.map((item, index) => {
          const state = index < activeIndex ? "done" : index === activeIndex ? "active" : "waiting";
          return (
            <li key={item.title} className={`loading-step loading-step--${state}`} aria-current={state === "active" ? "step" : undefined}>
              <span className="loading-step__marker">{state === "done" ? "✓" : index + 1}</span>
              <span>
                <strong>{item.title}</strong>
                <small>{item.detail}</small>
              </span>
              {state === "active" ? <span className="step-activity" aria-label="Currently running"><i /><i /><i /></span> : null}
            </li>
          );
        })}
      </ol>
    </section>
  );
}

export function ProcessOverview() {
  return (
    <section className="process-card" aria-labelledby="process-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Workflow</p>
          <h2 id="process-title">How an investigation works</h2>
        </div>
        <p>IssuePilot keeps every stage reviewable and runs repository code only inside disposable Docker containers.</p>
      </div>
      <div className="process-grid">
        {stages.map((stage, index) => (
          <article key={stage.title} className="process-step">
            <span>{String(index + 1).padStart(2, "0")}</span>
            <h3>{stage.title}</h3>
            <p>{stage.detail}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
