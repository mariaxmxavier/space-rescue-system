/** Build accessible forms for the supported quote lifecycle operations.
 *
 * What: provides explicit, typed controls and displays each complete API result.
 * When called: the Quotes capability is mounted in the Operations workspace.
 * Why: quote outcomes and capacity transfer must remain controlled by the API.
 */
export function renderQuoteActions({ content, workspace, outcomes }) {
  appendCommandForm(content, {
    title: "Request quotes",
    operation: "request_quotes",
    button: "Request quotes",
    fields: [field("Mission ID", "mission_id"), field("Current time", "now", "number"), field("Response deadline", "response_deadline", "number", true)],
    workspace,
    outcomes,
  });
  appendCommandForm(content, {
    title: "Record a quote",
    operation: "record_quote",
    button: "Record quote",
    fields: [field("Offer ID", "offer_id"), field("RFQ ID", "rfq_id"), field("Offered seats", "offered_seats", "integer"), field("Arrival estimate", "arrival_estimate_seconds", "number"), field("Expires at", "expires_at", "number"), field("Recorded at", "recorded_at", "number"), field("Current time", "now", "number")],
    workspace,
    outcomes,
    nested: "offer",
  });
  appendCommandForm(content, {
    title: "Accept a quote",
    operation: "accept_quote",
    button: "Accept quote",
    fields: [field("Command ID", "command_id"), field("Mission ID", "mission_id"), field("Quote ID", "quote_id"), field("Current time", "now", "number"), field("Response deadline", "response_deadline", "number", true), field("Decision ID", "decision_id", "text", true), field("Revision ID", "revision_id", "text", true)],
    workspace,
    outcomes,
  });
  appendCommandForm(content, {
    title: "Reject a quote",
    operation: "reject_quote",
    button: "Reject quote",
    fields: [field("Quote ID", "quote_id"), field("Current time", "now", "number")],
    workspace,
    outcomes,
  });
  appendScalarForm(content, workspace, outcomes);
}

function field(label, name, type = "text", optional = false) {
  return { label, name, type, optional };
}

function appendCommandForm(parent, { title, operation, button, fields, workspace, outcomes, nested }) {
  const form = makeForm(title, fields);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(form));
    for (const item of fields) {
      if (item.optional && data[item.name] === "") delete data[item.name];
      if (item.type === "integer" && data[item.name] !== undefined) data[item.name] = Number(data[item.name]);
    }
    const payload = nested ? { command: { [nested]: Object.fromEntries(Object.entries(data).filter(([key]) => key !== "now")), now: data.now } } : { command: data };
    await submit(form, workspace, outcomes, operation, payload);
  });
  parent.append(form);
}

function appendScalarForm(parent, workspace, outcomes) {
  const form = makeForm("Expire quotes", [field("Current time", "now", "number")]);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(form));
    await submit(form, workspace, outcomes, "expire_quotes", data);
  });
  parent.append(form);
}

function makeForm(title, fields) {
  const form = document.createElement("form");
  form.className = "operation-form";
  const heading = document.createElement("h3");
  heading.textContent = title;
  form.append(heading);
  for (const item of fields) {
    const label = document.createElement("label");
    label.textContent = item.optional ? `${item.label} (optional)` : item.label;
    const input = document.createElement("input");
    input.name = item.name;
    input.type = item.type === "integer" || item.type === "number" ? "number" : item.type;
    if (item.type === "integer") input.step = "1";
    input.required = !item.optional;
    label.append(input);
    form.append(label);
  }
  const button = document.createElement("button");
  button.type = "submit";
  button.textContent = title === "Accept a quote" ? "Accept quote" : title === "Reject a quote" ? "Reject quote" : title === "Record a quote" ? "Record quote" : title;
  form.append(button);
  const result = document.createElement("div");
  result.className = "form-result";
  result.setAttribute("aria-live", "polite");
  form.append(result);
  return form;
}

async function submit(form, workspace, outcomes, operation, payload) {
  const button = form.querySelector("button[type=submit]");
  button.disabled = true;
  const resultTarget = form.querySelector(".form-result");
  try {
    const result = await workspace.invoke(operation, payload);
    outcomes.render(result, { operation, label: operation.replaceAll("_", " "), target: resultTarget });
    if (result?.status === "rejected" && result?.reason) {
      const alert = document.createElement("p");
      alert.setAttribute("role", "alert");
      alert.textContent = result.reason;
      resultTarget.prepend(alert);
    }
  } catch (error) {
    resultTarget.replaceChildren();
    const alert = document.createElement("p");
    alert.setAttribute("role", "alert");
    alert.textContent = error.message;
    resultTarget.append(alert);
  } finally {
    button.disabled = false;
  }
}
