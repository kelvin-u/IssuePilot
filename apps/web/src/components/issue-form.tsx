"use client";

import { FormEvent, useState } from "react";

type IssueFormProps = {
  onSubmit: (issueUrl: string) => Promise<void>;
};

export function IssueForm({ onSubmit }: IssueFormProps) {
  const [issueUrl, setIssueUrl] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await onSubmit(issueUrl);
      setIssueUrl("");
    } catch (submissionError) {
      setError(
        submissionError instanceof Error
          ? submissionError.message
          : "Something went wrong while starting the run.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      style={{
        display: "grid",
        gap: "1rem",
        padding: "1.25rem",
        borderRadius: "24px",
        background: "var(--panel)",
        border: "1px solid var(--line)",
        boxShadow: "0 18px 60px rgba(95, 64, 42, 0.10)",
      }}
    >
      <label style={{ display: "grid", gap: "0.5rem" }}>
        <span style={{ fontSize: "0.95rem", color: "var(--muted)" }}>
          Paste a GitHub issue URL
        </span>
        <input
          type="url"
          required
          value={issueUrl}
          onChange={(event) => setIssueUrl(event.target.value)}
          placeholder="https://github.com/owner/repo/issues/123"
          style={{
            padding: "0.95rem 1rem",
            borderRadius: "14px",
            border: "1px solid var(--line)",
            background: "#fff",
          }}
        />
      </label>

      <button
        type="submit"
        disabled={isSubmitting}
        style={{
          justifySelf: "start",
          padding: "0.9rem 1.25rem",
          borderRadius: "999px",
          border: "none",
          color: "#fffaf2",
          background: isSubmitting ? "#b99176" : "linear-gradient(135deg, var(--accent), var(--accent-dark))",
          cursor: isSubmitting ? "wait" : "pointer",
        }}
      >
        {isSubmitting ? "Agent is working..." : "Generate verified patch"}
      </button>

      {error ? (
        <p style={{ margin: 0, color: "#8b1e3f" }}>{error}</p>
      ) : null}
    </form>
  );
}
