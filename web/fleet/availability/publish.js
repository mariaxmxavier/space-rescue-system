/** What: publishes an exact availability revision. When: a registered ship reports capacity. Why: allocation must use current fleet availability. */
export function registerAvailability({ forms, workspace }) {
  forms.commandForm({
    operation: "publish_availability",
    title: "Publish ship availability",
    fields: [
      { name: "availability.availability_id", label: "Availability ID", required: true },
      { name: "availability.ship_id", label: "Ship ID", required: true },
      { name: "availability.total_seats", label: "Total seats", type: "number", required: true },
      { name: "availability.arrival_estimate_seconds", label: "Arrival estimate (seconds)", required: true },
      { name: "availability.available", label: "Available", type: "checkbox" },
      { name: "availability.recorded_at", label: "Recorded at (seconds)", required: true },
    ],
    onSubmit: (payload) => workspace.invoke("publish_availability", nested(payload)),
  });
}

/** What: nests dotted form names as API objects. When: a nested availability form submits. Why: the API expects its value object under availability. */
function nested(payload) {
  const availability = {};
  for (const [key, value] of Object.entries(payload.command)) {
    const field = key.replace("availability.", "");
    availability[field] = value;
  }
  return { command: { availability } };
}
