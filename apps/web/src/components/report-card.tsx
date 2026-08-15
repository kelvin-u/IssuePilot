import { RunRecord } from "../lib/api";

type ReportCardProps = {
  run: RunRecord | null;
};

export function ReportCard({ run }: ReportCardProps) {
  if (!run) {
    return null;
  }

  const { report } = run;
  const inspection = report.repository_inspection;
  const execution = report.command_execution;

  return (
    <section
      className="report-card"
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
      <div style={{ display: "grid", gap: "0.35rem" }}>
        <span style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
          Investigation report
        </span>
        <h2 style={{ margin: 0, fontSize: "1.5rem" }}>Agent assessment</h2>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "2fr 1fr",
          gap: "1rem",
        }}
      >
        <Panel title="Working hypothesis">
          <p style={{ margin: 0, color: "var(--muted)", lineHeight: 1.7 }}>
            {report.hypothesis}
          </p>
        </Panel>

        <Panel title="Confidence">
          <div
            style={{
              display: "inline-flex",
              width: "fit-content",
              padding: "0.35rem 0.75rem",
              borderRadius: "999px",
              background: "rgba(47, 111, 79, 0.12)",
              color: "var(--success)",
              textTransform: "capitalize",
            }}
          >
            {report.confidence}
          </div>
        </Panel>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: "1rem",
        }}
      >
        <Panel title="Evidence">
          <ul style={{ margin: 0, paddingLeft: "1.2rem", color: "var(--muted)", lineHeight: 1.7 }}>
            {report.evidence.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </Panel>

        <Panel title="Verification plan">
          <p style={{ margin: 0, color: "var(--muted)", lineHeight: 1.7 }}>
            {report.verification_summary}
          </p>
        </Panel>
      </div>

      <Panel title="Candidate patch preview">
        <pre
          style={{
            margin: 0,
            padding: "1rem",
            overflowX: "auto",
            borderRadius: "16px",
            background: "#2a211a",
            color: "#f8ead8",
            fontSize: "0.9rem",
            lineHeight: 1.6,
          }}
        >
          {report.patch_preview}
        </pre>
      </Panel>

      <div style={{ display: "grid", gap: "1rem" }}>
        <h3 style={{ margin: 0, fontSize: "1rem" }}>Reproduction command</h3>
        <Panel title={execution.selected_command || "No command selected"}>
          <div style={{ display: "grid", gap: "0.75rem" }}>
            <div style={{ color: "var(--muted)", lineHeight: 1.7 }}>
              Status: <span style={{ textTransform: "capitalize" }}>{execution.status}</span>
            </div>
            <p style={{ margin: 0, color: "var(--muted)", lineHeight: 1.7 }}>
              {execution.output_excerpt}
            </p>
            {execution.commands.length > 0 ? (
              <div style={{ display: "grid", gap: "0.65rem" }}>
                {execution.commands.map((command) => (
                  <article
                    key={command.command}
                    style={{
                      padding: "0.9rem 1rem",
                      borderRadius: "14px",
                      border: "1px solid var(--line)",
                      background: "#fffaf6",
                    }}
                  >
                    <strong>{command.label}</strong>
                    <div style={{ marginTop: "0.35rem", color: "var(--accent-dark)" }}>
                      {command.command}
                    </div>
                    <div style={{ marginTop: "0.35rem", color: "var(--muted)", lineHeight: 1.6 }}>
                      {command.reason}
                    </div>
                  </article>
                ))}
              </div>
            ) : null}
          </div>
        </Panel>
      </div>

      <div style={{ display: "grid", gap: "1rem" }}>
        <h3 style={{ margin: 0, fontSize: "1rem" }}>Repository inspection</h3>
        {inspection.status === "available" ? (
          <>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                gap: "1rem",
              }}
            >
              <Panel title="Search terms">
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                  {inspection.search_terms.map((term) => (
                    <span
                      key={term}
                      style={{
                        padding: "0.3rem 0.65rem",
                        borderRadius: "999px",
                        background: "rgba(201, 111, 45, 0.12)",
                        color: "var(--accent-dark)",
                      }}
                    >
                      {term}
                    </span>
                  ))}
                </div>
              </Panel>

              <Panel title="Candidate files">
                <ul style={{ margin: 0, paddingLeft: "1.2rem", color: "var(--muted)", lineHeight: 1.7 }}>
                  {inspection.candidate_files.map((path) => (
                    <li key={path}>{path}</li>
                  ))}
                </ul>
              </Panel>
            </div>

            <Panel title="Search hits">
              <div style={{ display: "grid", gap: "0.75rem" }}>
                {inspection.search_hits.map((hit) => (
                  <article
                    key={`${hit.path}:${hit.line_number}:${hit.line}`}
                    style={{
                      padding: "0.9rem 1rem",
                      borderRadius: "14px",
                      border: "1px solid var(--line)",
                      background: "#fffaf6",
                    }}
                  >
                    <div style={{ fontSize: "0.9rem", color: "var(--accent-dark)" }}>
                      {hit.path}:{hit.line_number}
                    </div>
                    <div style={{ marginTop: "0.35rem", color: "var(--muted)", lineHeight: 1.6 }}>
                      {hit.line || "(blank line match)"}
                    </div>
                  </article>
                ))}
              </div>
            </Panel>

            <div style={{ display: "grid", gap: "0.75rem" }}>
              <h4 style={{ margin: 0, fontSize: "1rem" }}>File snippets</h4>
              {inspection.file_snippets.map((snippet) => (
                <Panel key={snippet.path} title={snippet.path}>
                  <pre
                    style={{
                      margin: 0,
                      padding: "1rem",
                      overflowX: "auto",
                      borderRadius: "16px",
                      background: "#2a211a",
                      color: "#f8ead8",
                      fontSize: "0.85rem",
                      lineHeight: 1.6,
                    }}
                  >
                    {snippet.excerpt}
                  </pre>
                </Panel>
              ))}
            </div>
          </>
        ) : (
          <Panel title="Repository inspection status">
            <p style={{ margin: 0, color: "var(--muted)", lineHeight: 1.7 }}>
              Repository inspection will populate after a successful clone. If cloning fails,
              IssuePilot keeps the issue analysis but waits for workspace access before code search.
            </p>
          </Panel>
        )}
      </div>

      <div style={{ display: "grid", gap: "0.75rem" }}>
        <h3 style={{ margin: 0, fontSize: "1rem" }}>Artifacts</h3>
        {report.artifacts.map((artifact) => (
          <Panel key={artifact.label} title={artifact.label}>
            <p style={{ margin: 0, color: "var(--muted)", lineHeight: 1.7 }}>
              {artifact.content}
            </p>
          </Panel>
        ))}
      </div>
    </section>
  );
}

function Panel({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <article
      style={{
        display: "grid",
        gap: "0.75rem",
        padding: "1rem",
        borderRadius: "18px",
        border: "1px solid var(--line)",
        background: "#fff",
      }}
    >
      <strong>{title}</strong>
      {children}
    </article>
  );
}
