/**
 * What: builds labelled operation forms and complete accessible result views.
 * When called: the shell and capability modules need reusable browser controls.
 * Why: repeated form behaviour stays consistent while each capability owns its fields.
 */
export function createForms({ root, workspace, outcomes }) {
  function fieldMarkup(field) {
    const id = `field-${crypto.randomUUID()}`;
    const type = field.type === "number" ? "number" : field.type === "checkbox" ? "checkbox" : "text";
    const required = field.required ? " required" : "";
    const hint = field.hint ? `<small id="${id}-hint">${escapeHtml(field.hint)}</small>` : "";
    const input = type === "checkbox"
      ? `<input id="${id}" name="${escapeHtml(field.name)}" type="checkbox"${required}>`
      : `<input id="${id}" name="${escapeHtml(field.name)}" type="${type}"${field.type === "number" ? ' step="any"' : ''}${required}>`;
    return `<div class="field"><label for="${id}">${escapeHtml(field.label || field.name)}${required ? " *" : ""}</label>${input}${hint}</div>`;
  }

  function form({ operation, fields, command = false, title = operation, onSubmit }) {
    const section = document.createElement("section");
    section.className = "capability-card";
    section.innerHTML = `<h2>${escapeHtml(title)}</h2><form><div class="field-grid">${fields.map(fieldMarkup).join("")}</div><button type="submit">${escapeHtml(title)}</button><div class="form-result" aria-live="polite"></div></form>`;
    const formElement = section.querySelector("form");
    formElement.addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = formElement.querySelector("button");
      const result = section.querySelector(".form-result");
      const values = Object.fromEntries(fields.map((field) => {
        const control = formElement.elements.namedItem(field.name);
        if (field.optional && control.value === "") return [field.name, undefined];
        if (field.type === "checkbox") return [field.name, control.checked];
        if (field.type === "number") return [field.name, control.value === "" ? "" : Number(control.value)];
        return [field.name, control.value];
      }).filter(([, value]) => value !== undefined));
      button.disabled = true;
      button.dataset.label = button.textContent;
      button.textContent = "Submitting…";
      try {
        const payload = command ? { command: values } : values;
        const answer = onSubmit ? await onSubmit(payload) : await workspace.invoke(operation, payload);
        outcomes.render(answer, { operation, label: title, target: result });
      } catch (error) {
        result.replaceChildren();
        const alert = document.createElement("p");
        alert.setAttribute("role", "alert");
        alert.textContent = error.message;
        result.append(alert);
      } finally {
        button.disabled = false;
        button.textContent = button.dataset.label;
      }
    });
    root.append(section);
    return section;
  }

  return Object.freeze({
    commandForm: (options) => form({ ...options, command: true }),
    scalarForm: (options) => form(options),
  });
}

/** What: escapes user-facing text before it enters a generated label. When: a form renders. Why: user data stays text, not markup. */
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character]);
}

/**
 * What: renders the full API result in a concise summary and a disclosure.
 * When called: an operation completes or its result is inspected.
 * Why: callers can quickly read status and still inspect every returned field.
 */
export function createOutcomes() {
  return Object.freeze({
    render(result, { operation = "Operation", label = operation, target } = {}) {
      const container = target || document.createElement("div");
      container.replaceChildren();
      const summary = document.createElement("p");
      summary.className = "result-summary";
      const status = result?.status || "completed";
      summary.textContent = `${label}: ${status}${result?.reason ? ` — ${result.reason}` : ""}`;
      if (status === "rejected") summary.setAttribute("role", "alert");
      container.append(summary);
      const details = document.createElement("details");
      const title = document.createElement("summary");
      title.textContent = "Complete result";
      const pre = document.createElement("pre");
      pre.textContent = JSON.stringify(result, null, 2);
      details.append(title, pre);
      container.append(details);
      return container;
    },
  });
}
