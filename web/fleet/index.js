import { registerShips } from "./ships/register.js";
import { registerAvailability } from "./availability/publish.js";
import { registerOffers } from "./offers/publish.js";

/** What: registers fleet use cases. When: the shell composes Operations. Why: ships, availability and offers are one operator capability. */
export function registerFleet(context) {
  registerShips(context);
  registerAvailability(context);
  registerOffers(context);
}
