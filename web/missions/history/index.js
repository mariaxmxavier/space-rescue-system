/**
 * What: provides mission progress and the mission's ordered seat-change history.
 * When called: the shell mounts mission inspection within the active run.
 * Why: mission history explains confirmed and released seats independently of API call history.
 */
export function registerMissionHistory({ root, workspace, forms, outcomes }) {
  const section = document.createElement("section");
  section.setAttribute("aria-labelledby", "mission-history-heading");
  const heading = document.createElement("h2");
  heading.id = "mission-history-heading";
  heading.textContent = "Missions";
  section.append(heading);
  const result = document.createElement("div");
  result.setAttribute("aria-live", "polite");
  forms.scalarForm({
    operation: "get_progress",
    title: "Mission progress",
    fields: [
      { name: "mission_id", label: "Mission ID", required: true },
      { name: "now", label: "Current time", required: true },
    ],
    onSubmit: (payload) => workspace.invoke("get_progress", payload),
  });
  forms.scalarForm({
    operation: "get_history",
    title: "Mission history",
    fields: [{ name: "mission_id", label: "Mission ID", required: true }],
    onSubmit: async (payload) => {
      const answer = await workspace.invoke("get_history", payload);
      outcomes.render(answer, { operation: "get_history", label: "Mission history", target: result });
      return answer;
    },
  });
  section.append(result);
  root.append(section);
  return () => section.remove();
}
