/** What: registers ship response entry. When: Operations loads. Why: message identity and timing are required to preserve delivery semantics. */
export function registerResponses({ forms }) {
  forms.commandForm({
    operation: "record_response",
    title: "Record response (final outcome for this message)",
    fields: [
      { name: "message_id", label: "Message ID", required: true },
      { name: "delivery_id", label: "Delivery ID", required: true },
      { name: "attempt_number", label: "Attempt number", type: "number", required: true },
      { name: "request_id", label: "Request ID", required: true },
      { name: "outcome", label: "Outcome (ACCEPTED, PARTIALLY_ACCEPTED or REFUSED)", required: true },
      { name: "confirmed_seats", label: "Confirmed seats", type: "number", required: true },
      { name: "sent_at", label: "Sent at (seconds)", required: true },
      { name: "received_at", label: "Received at (seconds)", optional: true },
      { name: "communication_rtt_seconds", label: "Communication round-trip time (seconds)", optional: true },
    ],
  });
}
