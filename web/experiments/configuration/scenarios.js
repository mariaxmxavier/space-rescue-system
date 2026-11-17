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
  const revision = number(form, "Policy revision", "1", 1);
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
    value: () => {
      requireValid(form, "Complete the required mobilisation policy fields before creating the run.");
      return {
        policy_id: policyId.value,
        revision: Number(revision.value),
        name: name.value,
        selection_criteria: strategy.value,
      };
    },
  };
}

function makeScenarioForm() {
  const form = document.createElement("fieldset");
  const legend = document.createElement("legend");
  legend.textContent = "Scenario";
  form.append(legend);
  const scenarioId = input(form, "Scenario ID");
  const revision = number(form, "Scenario revision", "1", 1);
  const name = input(form, "Scenario name");
  const horizon = number(form, "Time horizon seconds", "3600");
  const seed = number(form, "Seed", "1");
  const budget = number(form, "Event budget", "100", 1);
  const baselineHeading = document.createElement("h4");
  baselineHeading.textContent = "Baseline mission and fleet";
  const missionId = input(form, "Baseline mission ID");
  const station = input(form, "Baseline station name");
  const people = number(form, "Baseline people to rescue", "1", 1);
  const createdAt = number(form, "Baseline mission created at", "0");
  const marketId = input(form, "Baseline market ID");
  const shipId = input(form, "Baseline ship ID");
  const shipName = input(form, "Baseline ship name");
  const seats = number(form, "Baseline ship total seats", "1", 1);
  const arrival = number(form, "Baseline arrival estimate seconds", "0");
  const available = document.createElement("input");
  available.type = "checkbox";
  available.checked = true;
  available.setAttribute("aria-label", "Baseline ship available");
  const availabilityId = input(form, "Baseline availability ID");
  const recordedAt = number(form, "Baseline availability recorded at", "0");
  form.append(baselineHeading);
  const availableLabel = document.createElement("label");
  availableLabel.append(available, document.createTextNode("Baseline ship available"));
  form.append(availableLabel);
  return {
    form,
    value: () => {
      requireValid(form, "Complete the required scenario and baseline fields before creating the run.");
      return {
      scenario_id: scenarioId.value,
      revision: Number(revision.value),
      name: name.value,
      time_horizon_seconds: horizon.value,
      seed: Number(seed.value),
      event_budget: Number(budget.value),
      baseline: {
        missions: [{
          mission_id: missionId.value,
          station_name: station.value,
          people_count: Number(people.value),
          created_at: createdAt.value,
          requests: [],
          history: [],
        }],
        market: {
          market_id: marketId.value,
          ships: [{ ship_id: shipId.value, name: shipName.value }],
          availabilities: [{
            availability_id: availabilityId.value,
            ship_id: shipId.value,
            total_seats: Number(seats.value),
            arrival_estimate_seconds: arrival.value,
            available: available.checked,
            recorded_at: recordedAt.value,
          }],
          rfqs: [],
          quotes: [],
          offers: [],
          quote_history: [],
        },
        command_index: [],
        message_index: [],
        delivery_index: [],
        decision_index: [],
        session_index: [],
      },
      response_rules: [],
      availability_changes: [],
      communication_profiles: [],
      };
    },
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

function number(parent, label, value, minimum = 0) {
  const control = input(parent, label);
  control.type = "number";
  control.min = String(minimum);
  control.value = value;
  return control;
}

/** What: validates one policy or scenario editor before collecting its payload. When: a run is created. Why: users receive a local field error instead of an opaque API rejection. */
function requireValid(form, message) {
  const invalid = [...form.querySelectorAll("input, select")].find((control) => !control.checkValidity());
  if (!invalid) return;
  invalid.reportValidity();
  throw new Error(message);
}
