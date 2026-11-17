/**
 * What: provides explicit inbound synchronisation and report recovery actions.
 * When called: the Communication capability is mounted in Exploration.
 * Why: session controls must be visible and returned sequence positions inspectable.
 */
export function registerCommunicationRecovery({ root, workspace, outcomes }) {
  command(root, workspace, outcomes, {
    title: "Synchronise inbound",
    operation: "synchronise_inbound",
    fields: [
      { name: "session_id", label: "Session ID" },
      { name: "version", label: "Version", type: "number" },
      { name: "next_sequence", label: "Next sequence", type: "number" },
    ],
    after: (value) => value,
  });
  command(root, workspace, outcomes, {
    title: "Recover reports",
    operation: "recover_reports",
    fields: [
      { name: "session_id", label: "Session ID" },
      { name: "version", label: "Version", type: "number" },
      { name: "from_sequence", label: "From sequence", type: "number" },
      { name: "count", label: "Count", type: "number" },
    ],
  });
}

function command(root, workspace, outcomes, { title, operation, fields }) {
  const form = document.createElement("form");
  for (const field of fields) {
    const label = document.createElement("label");
    label.textContent = field.label;
    const input = document.createElement("input");
    input.name = field.name;
    input.type = field.type ?? "text";
    input.required = true;
    if (field.type === "number") input.step = "1";
    label.append(input);
    form.append(label);
  }
  const button = document.createElement("button");
  button.type = "submit";
  button.textContent = title;
  const result = document.createElement("div");
  result.setAttribute("aria-live", "polite");
  form.append(button);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    button.disabled = true;
    const value = Object.fromEntries(new FormData(form));
    for (const field of fields.filter((item) => item.type === "number")) {
      value[field.name] = Number(value[field.name]);
    }
    try {
      const answer = await workspace.invoke(operation, { command: value });
      outcomes.render(answer, { operation, label: title, target: result });
    } catch (error) {
      const alert = document.createElement("p");
      alert.setAttribute("role", "alert");
      alert.textContent = error.message;
      result.replaceChildren(alert);
    } finally {
      button.disabled = false;
    }
  });
  root.append(form, result);
}
