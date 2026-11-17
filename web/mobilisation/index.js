import { registerMobilisationAction } from "./actions/mobilise.js";

/** What: registers mobilisation actions. When: the shell composes Operations. Why: strategy decisions remain owned by the rescue application. */
export function registerMobilisation(context) {
  registerMobilisationAction(context);
}
