import { RunRecord } from "../lib/api";

type RunStatusProps = {
  run: RunRecord | null;
};

export function RunStatus({ run }: RunStatusProps) {
  if (!run) {
    return (
      <section
        className="run-status-card"
        style={{
          padding: "1.25rem",
          borderRadius: "24px",
          border: "1px dashed var(--line)",
          color: "var(--muted)",
          background: "rgba(255, 250, 242, 0.6)",
        }}
      >
        No run yet. Start with a GitHub issue URL and IssuePilot will build an
        evidence-backed patch report.
      </section>
    );
  }

  return (
    <section
      className="run-status-card"
      style={{
        display: "grid",
        gap: "1rem",
        padding: "1.5rem",
        borderRadius: "24px",
        border: "1px solid var(--line)",
        background: "var(--panel)",
        boxShadow: "0 18px 60px rgba(95, 64, 42, 0.10)",
      }}
    >
      <div style={{ display: "grid", gap: "0.3rem" }}>
        <span style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
          {run.issue.repository} #{run.issue.issue_number}
        </span>
        <h2 style={{ margin: 0, fontSize: "1.6rem" }}>{run.issue.title}</h2>
        <p style={{ margin: 0, color: "var(--muted)" }}>{run.issue.summary}</p>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "0.8rem",
        }}
      >
        <Metric label="Run status" value={run.status} />
        <Metric label="Suspected area" value={run.issue.suspected_area} />
        <Metric label="Workspace status" value={run.workspace.status} />
        <Metric label="Sandbox runtime" value={run.workspace.sandbox.runtime} />
      </div>

      <details className="workspace-details">
        <summary>Technical workspace details</summary>
        <div className="workspace-details__content">
        <div style={{ color: "var(--muted)", lineHeight: 1.6 }}>
          Job directory: {run.workspace.job_dir}
        </div>
        <div style={{ color: "var(--muted)", lineHeight: 1.6 }}>
          Repo directory: {run.workspace.repo_dir}
        </div>
        <div style={{ color: "var(--muted)", lineHeight: 1.6 }}>
          Clone URL: {run.workspace.clone_url}
        </div>
        <div style={{ color: "var(--muted)", lineHeight: 1.6 }}>
          Launch hint: {run.workspace.sandbox.launch_hint}
        </div>
        </div>
      </details>

      <div style={{ display: "grid", gap: "0.75rem" }}>
        <h3 style={{ margin: 0, fontSize: "1rem" }}>Investigation timeline</h3>
        {run.steps.map((step) => (
          <article
            key={step.title}
            style={{
              padding: "0.95rem 1rem",
              borderRadius: "16px",
              border: "1px solid var(--line)",
              background: "#fff",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                gap: "1rem",
                alignItems: "center",
              }}
            >
              <strong>{step.title}</strong>
              <span
                style={{
                  color:
                    step.status === "completed"
                      ? "var(--success)"
                      : step.status === "failed"
                        ? "#8b1e3f"
                        : "var(--muted)",
                  textTransform: "capitalize",
                }}
              >
                {step.status}
              </span>
            </div>
            <p style={{ marginBottom: 0, color: "var(--muted)" }}>{step.detail}</p>
          </article>
        ))}
      </div>

      <div style={{ display: "grid", gap: "0.5rem" }}>
        <h3 style={{ margin: 0, fontSize: "1rem" }}>Workspace notes</h3>
        {run.workspace.notes.map((note) => (
          <div
            key={note}
            style={{
              padding: "0.85rem 1rem",
              borderRadius: "14px",
              border: "1px solid var(--line)",
              background: "#fff",
              color: "var(--muted)",
            }}
          >
            {note}
          </div>
        ))}
      </div>

      <div style={{ color: "var(--muted)" }}>{run.recommendation}</div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        padding: "1rem",
        borderRadius: "18px",
        border: "1px solid var(--line)",
        background: "#fff",
      }}
    >
      <div style={{ fontSize: "0.85rem", color: "var(--muted)" }}>{label}</div>
      <div style={{ marginTop: "0.4rem", lineHeight: 1.4 }}>{value}</div>
    </div>
  );
}
