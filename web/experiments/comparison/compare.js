/**
 * What: submits policy comparisons and displays results with baseline context.
 * When called: the Experiments capability mounts on a selected run.
 * Why: simulated results must not be mistaken for live mission state.
 */
export function registerComparison({ root, workspace, outcomes, configuration }) {
  const form = document.createElement("form");
  const scenarioId = field(form, "Scenario ID");
  const revision = field(form, "Scenario revision", "number");
  const policyId = field(form, "Policy ID");
  const policyRevision = field(form, "Policy revision", "number");
  const button = document.createElement("button");
  button.type = "submit";
  button.textContent = "Compare policies";
  form.append(button);
  const result = document.createElement("section");
  result.setAttribute("aria-live", "polite");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    result.replaceChildren();
    if (!scenarioId.value.trim()) {
      const alert = document.createElement("p");
      alert.setAttribute("role", "alert");
      alert.textContent = "A configured scenario is required before comparison.";
      result.append(alert);
      return;
    }
    const configuredPolicies = configuration.values().policies;
    const policyKeys = configuredPolicies.length
      ? configuredPolicies.map((policy) => [policy.policy_id, policy.revision])
      : policyId.value.trim() ? [[policyId.value, Number(policyRevision.value)]] : [];
    if (policyKeys.length === 0) {
      const alert = document.createElement("p");
      alert.setAttribute("role", "alert");
      alert.textContent = "A configured policy is required before comparison.";
      result.append(alert);
      return;
    }
    button.disabled = true;
    result.append(statusLabel("Live mission: current rescue run"));
    try {
      const answer = await workspace.invoke("compare", {
        command: {
          scenario_id: scenarioId.value,
          scenario_revision: Number(revision.value),
          policy_keys: policyKeys,
        },
      });
      const heading = statusLabel("Simulation baseline: configured scenario");
      result.append(heading);
      outcomes.render(answer, { operation: "compare", label: "Simulation comparison", target: result });
    } catch (error) {
      const alert = document.createElement("p");
      alert.setAttribute("role", "alert");
      alert.textContent = error.message;
      result.append(alert);
    } finally {
      button.disabled = false;
    }
  });
  root.append(form, result);
}

function field(form, labelText, type = "text") {
  const label = document.createElement("label");
  label.textContent = labelText;
  const input = document.createElement("input");
  input.setAttribute("aria-label", labelText);
  input.type = type;
  input.required = true;
  if (type === "number") {
    input.min = "1";
    input.value = "1";
  }
  label.append(input);
  form.append(label);
  return input;
}

function statusLabel(text) {
  const label = document.createElement("p");
  label.textContent = text;
  return label;
}
