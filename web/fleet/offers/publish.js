/** What: publishes a ship offer revision for a mission. When: a registered ship offers seats. Why: mobilisation works from authoritative offer revisions. */
export function registerOffers({ forms, workspace }) {
  forms.commandForm({
    operation: "publish_offer",
    title: "Publish ship offer",
    fields: [
      { name: "offer_id", label: "Offer ID", required: true },
      { name: "mission_id", label: "Mission ID", required: true },
      { name: "ship_id", label: "Ship ID", required: true },
      { name: "revision.revision_id", label: "Revision ID", required: true },
      { name: "revision.revision_number", label: "Revision number", type: "number", required: true },
      { name: "revision.capacity", label: "Seats offered", type: "number", required: true },
      { name: "revision.arrival_estimate_seconds", label: "Arrival estimate (seconds)", required: true },
      { name: "revision.available", label: "Available", type: "checkbox" },
      { name: "revision.recorded_at", label: "Recorded at (seconds)", required: true },
    ],
    onSubmit: (payload) => workspace.invoke("publish_offer", { command: {
      offer_id: payload.command.offer_id,
      mission_id: payload.command.mission_id,
      ship_id: payload.command.ship_id,
      revision: nestedValue(payload.command, "revision"),
    } }),
  });
}

/** What: extracts fields for one nested command object. When: an offer form submits. Why: transport receives the dataclass shape expected by the API. */
function nestedValue(fields, prefix) {
  return Object.fromEntries(Object.entries(fields)
    .filter(([key]) => key.startsWith(`${prefix}.`))
    .map(([key, value]) => [key.slice(prefix.length + 1), value]));
}
