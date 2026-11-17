/**
 * What: builds controls to inspect delivery attempts and session sequence state.
 * When called: the Communication capability is mounted in Exploration.
 * Why: the server's classifications and counters explain message handling.
 */
export function registerCommunicationInspection({ root, workspace, outcomes }) {
  scalar(root, workspace, outcomes, {
    title: "Inspect deliveries",
    operation: "get_deliveries",
    field: { label: "Message ID", name: "message_id" },
  });
  scalar(root, workspace, outcomes, {
    title: "Inspect session",
    operation: "get_session",
    field: { label: "Session ID", name: "session_id" },
  });
}

function scalar(root, workspace, outcomes, { title, operation, field }) {
  const form = document.createElement("form");
  const label = document.createElement("label");
  label.textContent = field.label;
  const input = document.createElement("input");
  input.name = field.name;
  input.required = true;
  label.append(input);
  const button = document.createElement("button");
  button.type = "submit";
  button.textContent = title;
  const result = document.createElement("div");
  result.setAttribute("aria-live", "polite");
  const resultHeading = document.createElement("h4");
  resultHeading.textContent = title === "Inspect deliveries" ? "Deliveries" : "Session details";
  result.append(resultHeading);
  form.append(label, button);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    button.disabled = true;
    try {
      const response = await workspace.invoke(operation, { [field.name]: input.value });
      outcomes.render(response, { operation, label: title, target: result });
    } catch (error) {
      showError(result, error);
    } finally {
      button.disabled = false;
    }
  });
  root.append(form, result);
}

function showError(target, error) {
  const alert = document.createElement("p");
  alert.setAttribute("role", "alert");
  alert.textContent = error.message;
  target.replaceChildren(alert);
}
