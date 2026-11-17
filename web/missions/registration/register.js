/** What: presents mission registration fields. When: Operations loads. Why: a rescue requires an identified station and positive demand. */
export function registerMission({ forms }) {
  forms.commandForm({
    operation: "register_mission",
    title: "Register mission",
    fields: [
      { name: "mission_id", label: "Mission ID", required: true },
      { name: "station_name", label: "Station name", required: true },
      { name: "people_count", label: "People count", type: "number", required: true, hint: "Enter a positive whole number." },
      { name: "created_at", label: "Created at (seconds)", required: true, hint: "Enter seconds as a decimal value, for example 0." },
    ],
  });
}
