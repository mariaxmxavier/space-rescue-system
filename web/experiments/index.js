/**
 * What: registers scenario and mobilisation policy experiment controls.
 * When called: the Exploration tab mounts the Experiments capability.
 * Why: users can compare strategies while preserving the live run as separate context.
 */
import { registerScenarioConfiguration } from "./configuration/scenarios.js";
import { registerComparison } from "./comparison/compare.js";

export function registerExperiments({ root, workspace, outcomes }) {
  const section = document.createElement("section");
  section.className = "capability-card";
  const heading = document.createElement("h2");
  heading.textContent = "Experiments";
  section.append(heading);
  const configuration = document.createElement("section");
  const configHeading = document.createElement("h3");
  configHeading.textContent = "Scenario and policy configuration";
  configuration.append(configHeading);
  const comparison = document.createElement("section");
  comparison.setAttribute("aria-label", "Policy comparison");
  section.append(configuration, comparison);
  const configurationState = registerScenarioConfiguration({ root: configuration, workspace });
  registerComparison({ root: comparison, workspace, outcomes, configuration: configurationState });
  root.replaceChildren(section);
  return Object.freeze({ getRunConfiguration: configurationState.values });
}
