/** What: adds an authoritative progress query. When: an operator needs current mission totals. Why: only committed API status determines rescue progress. */
export function registerMissionProgress({ forms }) {
  forms.scalarForm({
    operation: "get_progress",
    title: "Get progress",
    fields: [
      { name: "mission_id", label: "Mission ID", required: true },
      { name: "now", label: "Current time (seconds)", required: true },
    ],
  });
}
