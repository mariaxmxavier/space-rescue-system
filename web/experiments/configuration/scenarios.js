/**
 * What: lets users compose scenario and policy configuration for a run.
 * When called: the Experiments capability mounts.
 * Why: comparisons need configured, reproducible baselines and policy revisions.
 */
export function registerScenarioConfiguration({ root }) {
  const policies = [];
  const scenarios = [];
  const policyList = document.createElement("div");
  const scenarioList = document.createElement("div");
  const addPolicy = document.createElement("button");
  addPolicy.type = "button";
  addPolicy.textContent = "Add mobilisation policy";
  addPolicy.addEventListener("click", () => {
    const policy = makePolicyForm();
    policies.push(policy);
    policyList.append(policy.form);
  });
  const addScenario = document.createElement("button");
  addScenario.type = "button";
  addScenario.textContent = "Add scenario";
  addScenario.addEventListener("click", () => {
    const scenario = makeScenarioForm();
    scenarios.push(scenario);
    scenarioList.append(scenario.form);
  });
  const config = document.createElement("p");
  config.textContent = "Configure scenario baselines and policies when creating a run.";
  root.append(config, addPolicy, policyList, addScenario, scenarioList);
  return Object.freeze({
    values() {
      return {
        policies: policies.map((item) => item.value()),
        scenarios: scenarios.map((item) => item.value()),
      };
    },
  });
}

function makePolicyForm() {
  const form = document.createElement("fieldset");
  const legend = document.createElement("legend");
  legend.textContent = "Mobilisation policy";
  form.append(legend);
  const policyId = input(form, "Policy ID");
  const revision = number(form, "Policy revision", "1");
  const name = input(form, "Policy name");
  const strategy = document.createElement("select");
  strategy.setAttribute("aria-label", "Selection strategy");
  for (const value of ["earliest_arrival", "largest_capacity", "priority_queue", "min_cost_flow", "cp_sat", "knapsack"]) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    strategy.append(option);
  }
  form.append(strategy);
  return {
    form,
    value: () => ({
      policy_id: policyId.value,
      revision: revision.value,
      name: name.value,
      selection_criteria: strategy.value,
    }),
  };
}

function makeScenarioForm() {
  const form = document.createElement("fieldset");
  const legend = document.createElement("legend");
  legend.textContent = "Scenario";
  form.append(legend);
  const scenarioId = input(form, "Scenario ID");
  const revision = number(form, "Scenario revision", "1");
  const name = input(form, "Scenario name");
  const horizon = number(form, "Time horizon seconds", "3600");
  const seed = number(form, "Seed", "1");
  const budget = number(form, "Event budget", "100");
  const note = document.createElement("p");
  note.textContent = "A baseline mission and fleet are required before this scenario can be compared.";
  form.append(note);
  return {
    form,
    value: () => ({
      scenario_id: scenarioId.value,
      revision: revision.value,
      name: name.value,
      time_horizon_seconds: horizon.value,
      seed: seed.value,
      event_budget: budget.value,
      baseline: { missions: [], market: { ships: [] } },
      response_rules: [],
      availability_changes: [],
      communication_profiles: [],
    }),
  };
}

function input(parent, labelText) {
  const label = document.createElement("label");
  label.textContent = labelText;
  const control = document.createElement("input");
  control.setAttribute("aria-label", labelText);
  control.required = true;
  label.append(control);
  parent.append(label);
  return control;
}

function number(parent, label, value) {
  const control = input(parent, label);
  control.type = "number";
  control.min = "0";
  control.value = value;
  return control;
}
