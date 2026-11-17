import { registerRequestActions } from "./actions/index.js";

/** What: registers seat request use cases. When: the shell composes Operations. Why: requests need independent creation and closure controls. */
export function registerRequests(context) {
  registerRequestActions(context);
}
