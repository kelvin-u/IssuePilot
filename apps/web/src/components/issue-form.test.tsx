import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import { IssueForm } from "./issue-form";

test("submits a GitHub issue URL", async () => {
  const onSubmit = vi.fn().mockResolvedValue(undefined);
  render(<IssueForm onSubmit={onSubmit} />);
  fireEvent.change(screen.getByPlaceholderText("https://github.com/owner/repo/issues/123"), { target: { value: "https://github.com/acme/repo/issues/7" } });
  fireEvent.click(screen.getByRole("button", { name: "Investigate issue" }));
  await waitFor(() => expect(onSubmit).toHaveBeenCalledWith("https://github.com/acme/repo/issues/7"));
});
