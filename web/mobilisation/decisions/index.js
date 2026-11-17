/**
 * What: lets the operator inspect one recorded mobilisation decision and every returned explanation field.
 * When called: the shell mounts the decision inspection capability.
 * Why: allocation reasons and skipped candidates must remain auditable from the live run.
 */
export function registerDecisionInspection({ root, workspace, forms }) {
  const section = document.createElement("section");
  section.setAttribute("aria-labelledby", "decisions-heading");
  const heading = document.createElement("h2");
  heading.id = "decisions-heading";
  heading.textContent = "Decisions";
  section.append(heading);
  forms.scalarForm({
    operation: "get_decision",
    title: "Inspect decision",
    fields: [{ name: "decision_id", label: "Decision ID", required: true }],
    onSubmit: (payload) => workspace.invoke("get_decision", payload),
  });
  const latest = document.createElement("details");
  const summary = document.createElement("summary");
  summary.textContent = "Decision trace and allocation details";
  const body = document.createElement("pre");
  latest.append(summary, body);
  section.append(latest);
  const unsubscribe = workspace.subscribe(({ snapshot }) => {
    body.textContent = JSON.stringify(snapshot?.decision_index ?? [], null, 2);
  });
  root.append(section);
  return () => {
    unsubscribe();
    section.remove();
  };
}
