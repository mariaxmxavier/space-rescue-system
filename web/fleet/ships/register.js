/** What: presents ship registration. When: an operator adds a ship. Why: availability and offers require a known fleet identity. */
export function registerShips({ forms }) {
  forms.commandForm({
    operation: "register_ship",
    title: "Register ship",
    fields: [
      { name: "ship_id", label: "Ship ID", required: true },
      { name: "name", label: "Ship name", required: true },
    ],
  });
}
