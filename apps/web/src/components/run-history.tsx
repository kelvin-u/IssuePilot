import { RunRecord } from "../lib/api";

type RunHistoryProps = {
  runs: RunRecord[];
  activeRunId: string | null;
  onSelect: (run: RunRecord) => void;
};

export function RunHistory({ runs, activeRunId, onSelect }: RunHistoryProps) {
  return (
    <section
      className="run-history"
      style={{
        display: "grid",
        gap: "1rem",
        padding: "1.25rem",
        borderRadius: "24px",
        border: "1px solid var(--line)",
        background: "var(--panel)",
        boxShadow: "0 18px 60px rgba(95, 64, 42, 0.10)",
      }}
    >
      <div style={{ display: "grid", gap: "0.25rem" }}>
        <h2 style={{ margin: 0, fontSize: "1.2rem" }}>Recent runs</h2>
        <p style={{ margin: 0, color: "var(--muted)", lineHeight: 1.6 }}>
          Saved investigations stay available even after the backend restarts.
        </p>
      </div>

      {runs.length === 0 ? (
        <div style={{ color: "var(--muted)" }}>No saved runs yet.</div>
      ) : (
        <div style={{ display: "grid", gap: "0.75rem" }}>
          {runs.map((run) => {
            const isActive = activeRunId === run.id;
            return (
              <button
                key={run.id}
                type="button"
                onClick={() => onSelect(run)}
                style={{
                  textAlign: "left",
                  padding: "1rem",
                  borderRadius: "18px",
                  border: isActive ? "1px solid rgba(138, 69, 24, 0.45)" : "1px solid var(--line)",
                  background: isActive ? "rgba(201, 111, 45, 0.10)" : "#fff",
                  cursor: "pointer",
                }}
              >
                <div style={{ fontSize: "0.9rem", color: "var(--muted)" }}>
                  {run.issue.repository} #{run.issue.issue_number}
                </div>
                <div style={{ marginTop: "0.35rem", fontWeight: 600 }}>{run.issue.title}</div>
                <div
                  style={{
                    marginTop: "0.45rem",
                    display: "flex",
                    justifyContent: "space-between",
                    gap: "0.75rem",
                    color: "var(--muted)",
                    fontSize: "0.92rem",
                  }}
                >
                  <span style={{ textTransform: "capitalize" }}>{run.status}</span>
                  <span>{new Date(run.created_at).toLocaleString()}</span>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
}
