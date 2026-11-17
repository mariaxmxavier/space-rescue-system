/** What: submits a mobilisation request to the selected policy. When: an operator seeks remaining help. Why: the API owns ship allocation and seat accounting. */
export function registerMobilisationAction({ forms }) {
  forms.commandForm({
    operation: "mobilise",
    title: "Mobilise ships",
    fields: [
      { name: "mission_id", label: "Mission ID", required: true },
      { name: "policy_id", label: "Policy ID", required: true },
      { name: "policy_revision", label: "Policy revision", type: "number", required: true },
      { name: "now", label: "Current time (seconds)", required: true },
    ],
  });
}
