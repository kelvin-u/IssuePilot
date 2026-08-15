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
    <form onSubmit={handleSubmit} className="issue-form">
      <div className="issue-form__copy">
        <p className="eyebrow">New investigation</p>
        <h2>Enter a public issue URL</h2>
        <p>We’ll inspect the repository, attempt a reproduction, and only recommend a patch that passes verification.</p>
      </div>
      <div className="issue-form__controls">
        <label htmlFor="issue-url">GitHub issue URL</label>
        <div className="issue-form__row">
        <input
          id="issue-url"
          type="url"
          required
          value={issueUrl}
          onChange={(event) => setIssueUrl(event.target.value)}
          placeholder="https://github.com/owner/repo/issues/123"
        />
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? <><span className="button-spinner" aria-hidden="true" />Investigating</> : "Investigate issue"}
          </button>
        </div>
      </div>

      {error ? (
        <p className="form-error" role="alert">{error}</p>
      ) : null}
    </form>
  );
}
