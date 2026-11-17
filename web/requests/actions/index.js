/** What: adds direct request creation, cancellation and expiry. When: Operations loads. Why: each action delegates finality and accounting to the API. */
export function registerRequestActions({ forms }) {
  forms.commandForm({
    operation: "create_request",
    title: "Create request",
    fields: [
      { name: "command_id", label: "Command ID", required: true },
      { name: "mission_id", label: "Mission ID", required: true },
      { name: "ship_id", label: "Ship ID", required: true },
      { name: "requested_seats", label: "Seats requested", type: "number", required: true },
      { name: "revision_id", label: "Offer revision ID", required: true },
      { name: "now", label: "Current time (seconds)", required: true },
      { name: "response_deadline", label: "Response deadline (seconds)", optional: true },
      { name: "decision_id", label: "Decision ID", optional: true },
    ],
  });
  forms.commandForm({
    operation: "cancel_request",
    title: "Cancel request",
    fields: [
      { name: "mission_id", label: "Mission ID", required: true },
      { name: "request_id", label: "Request ID", required: true },
      { name: "now", label: "Current time (seconds)", required: true },
      { name: "reason", label: "Reason", required: true },
    ],
  });
  forms.commandForm({
    operation: "expire_request",
    title: "Expire request",
    fields: [
      { name: "mission_id", label: "Mission ID", required: true },
      { name: "request_id", label: "Request ID", required: true },
      { name: "now", label: "Current time (seconds)", required: true },
    ],
  });
}
