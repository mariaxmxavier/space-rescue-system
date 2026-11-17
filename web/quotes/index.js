/** Register quote operations and market holds in the Operations workspace.
 *
 * What: exposes quote solicitation, recording, acceptance, rejection and expiry.
 * When called: the shell registers the Quotes capability for the selected run.
 * Why: operators need a guided way to manage held capacity before it becomes a request.
 */
import { renderQuoteActions } from "./lifecycle/actions.js";
import { renderQuoteHoldSummary } from "./request/holds.js";

export function registerQuotes({ root, workspace, outcomes }) {
  const content = document.createElement("section");
  content.className = "capability quotes";
  content.setAttribute("aria-labelledby", "quotes-heading");
  const heading = document.createElement("h2");
  heading.id = "quotes-heading";
  heading.textContent = "Quotes";
  content.append(heading);

  let holds = renderQuoteHoldSummary(workspace.getSnapshot()?.snapshot);
  content.append(holds);
  renderQuoteActions({ content, workspace, outcomes });
  root.replaceChildren(content);
  const unsubscribe = workspace.subscribe(() => {
    const current = renderQuoteHoldSummary(workspace.getSnapshot()?.snapshot);
    holds.replaceWith(current);
    holds = current;
  });
  return unsubscribe;
}
