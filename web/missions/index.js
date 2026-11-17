import { registerMission } from "./registration/register.js";
import { registerMissionProgress } from "./progress/read.js";

/** What: registers mission use cases in the browser. When: the shell composes Operations. Why: mission input and status remain grouped by capability. */
export function registerMissions(context) {
  registerMission(context);
  registerMissionProgress(context);
}
