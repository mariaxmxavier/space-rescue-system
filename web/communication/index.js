/**
 * What: registers communication inspection and recovery controls.
 * When called: the exploration tab mounts the Communication capability.
 * Why: operators need to inspect delivery decisions and recover session reports.
 */
import { registerCommunicationInspection } from "./inspection/deliveries.js";
import { registerCommunicationRecovery } from "./recovery/actions.js";

export function registerCommunication({ root, workspace, outcomes }) {
  const section = document.createElement("section");
  section.className = "capability-card";
  const heading = document.createElement("h2");
  heading.textContent = "Communication";
  section.append(heading);
  const inspection = document.createElement("section");
  const inspectionHeading = document.createElement("h3");
  inspectionHeading.textContent = "Delivery inspection";
  inspection.append(inspectionHeading);
  section.append(inspection);
  const recovery = document.createElement("section");
  const recoveryHeading = document.createElement("h3");
  recoveryHeading.textContent = "Session recovery";
  recovery.append(recoveryHeading);
  section.append(recovery);
  registerCommunicationInspection({ root: inspection, workspace, outcomes });
  registerCommunicationRecovery({ root: recovery, workspace, outcomes });
  root.replaceChildren(section);
}
