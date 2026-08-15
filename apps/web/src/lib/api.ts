export type RunStep = {
  title: string;
  detail: string;
  status: "pending" | "completed" | "failed";
};

export type RunRecord = {
  id: string;
  status: "queued" | "investigating" | "needs_review" | "completed" | "failed";
  created_at: string;
  issue: {
    title: string;
    repository: string;
    issue_number: number;
    summary: string;
    suspected_area: string;
  };
  workspace: {
    job_dir: string;
    repo_dir: string;
    clone_url: string;
    status: "ready" | "clone_failed";
    sandbox: {
      runtime: "python" | "node" | "generic";
      docker_context: string;
      launch_hint: string;
    };
    notes: string[];
  };
  steps: RunStep[];
  report: {
    hypothesis: string;
    evidence: string[];
    verification_summary: string;
    confidence: string;
    patch_preview: string;
    repository_inspection: {
      status: "available" | "unavailable";
      search_terms: string[];
      discovered_files: string[];
      candidate_files: string[];
      search_hits: {
        path: string;
        line_number: number;
        line: string;
      }[];
      file_snippets: {
        path: string;
        excerpt: string;
      }[];
    };
    command_execution: {
      status: "planned" | "succeeded" | "failed" | "skipped";
      selected_command: string;
      output_excerpt: string;
      exit_code: number | null;
      container_image: string;
      commands: {
        label: string;
        command: string;
        reason: string;
      }[];
    };
    patch_proposal: {
      status: "generated" | "not_configured" | "failed" | "rejected" | "skipped";
      provider: string;
      model: string;
      summary: string;
      root_cause: string;
      rationale: string;
      unified_diff: string;
      changed_files: string[];
      tests_to_run: string[];
      error: string;
    };
    patch_application: {
      status: "not_attempted" | "applied" | "rejected" | "failed";
      changed_files: string[];
      diff_stat: string;
      message: string;
    };
    verification: {
      status: "not_run" | "passed" | "failed" | "skipped";
      command: string;
      exit_code: number | null;
      output_excerpt: string;
      baseline_failed: boolean;
    };
    artifacts: {
      label: string;
      content: string;
    }[];
  };
  recommendation: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type JobRecord = {
  id: string;
  status: "queued" | "running" | "completed" | "failed" | "cancel_requested" | "cancelled";
  run_id: string | null;
  error: string;
  stage: string;
  stage_detail: string;
};

export type JobProgress = Pick<JobRecord, "status" | "stage" | "stage_detail">;

export async function intakeIssue(
  issueUrl: string,
  onProgress?: (progress: JobProgress) => void,
): Promise<RunRecord> {
  const response = await fetch(`${API_URL}/api/v1/issues/intake`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ issue_url: issueUrl }),
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? "Failed to create investigation run");
  }

  const job = (await response.json()) as JobRecord;
  onProgress?.(job);
  for (;;) {
    const statusResponse = await fetch(`${API_URL}/api/v1/jobs/${job.id}`, { cache: "no-store" });
    if (!statusResponse.ok) throw new Error("Failed to read investigation job");
    const current = (await statusResponse.json()) as JobRecord;
    onProgress?.(current);
    if (current.status === "completed" && current.run_id) return getRun(current.run_id);
    if (current.status === "failed" || current.status === "cancelled") {
      throw new Error(current.error || `Investigation ${current.status}`);
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
}

export async function getRun(runId: string): Promise<RunRecord> {
  const response = await fetch(`${API_URL}/api/v1/runs/${runId}`, { cache: "no-store" });
  if (!response.ok) throw new Error("Failed to load investigation run");
  return response.json();
}

export async function listRuns(): Promise<RunRecord[]> {
  const response = await fetch(`${API_URL}/api/v1/runs`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Failed to load run history");
  }

  return response.json();
}
