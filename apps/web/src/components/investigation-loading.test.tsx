import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { InvestigationLoading, ProcessOverview } from "./investigation-loading";

test("explains the workflow before submission", () => {
  render(<ProcessOverview />);
  expect(screen.getByRole("heading", { name: "How an investigation works" })).toBeVisible();
  expect(screen.getByText("Reproduce the problem")).toBeVisible();
  expect(screen.getByText("Verify the result")).toBeVisible();
});

test("shows a clear investigation state for the submitted issue", () => {
  const { container } = render(
    <InvestigationLoading
      issueUrl="https://github.com/acme/repo/issues/7"
      stage="inspecting_repository"
      stageDetail="Searching the repository for relevant code and evidence."
    />,
  );
  expect(screen.getByRole("heading", { name: "Investigating issue" })).toBeVisible();
  expect(screen.getByText("https://github.com/acme/repo/issues/7")).toBeVisible();
  expect(screen.getByText("This can take a few minutes.", { exact: false })).toBeVisible();
  expect(container.querySelector('[aria-current="step"]')).toHaveTextContent("Find the relevant code");
});
