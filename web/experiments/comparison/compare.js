/** Compare configured policies against one immutable scenario baseline.
 * When Exploration mounts, explicit policy rows and retained complete results
 * make comparison inputs independent of drafts intended for a future run.
 */
export function registerComparison({ root, workspace, outcomes }) {
  const form = document.createElement('form'); form.dataset.operation = 'compare';
  const heading = document.createElement('h4'); heading.textContent = 'Compare configured policies';
  form.append(heading);
  const scenarioId = field(form, 'Scenario ID');
  const revision = field(form, 'Scenario revision', 'number');
  const rows = [];
  const list = document.createElement('div');
  const add = document.createElement('button'); add.type = 'button'; add.textContent = 'Add comparison policy';
  function addPolicy() {
    const group = document.createElement('fieldset');
    const legend = document.createElement('legend'); legend.textContent = `Comparison policy ${rows.length + 1}`; group.append(legend);
    const id = field(group, 'Policy ID');
    const revision = field(group, 'Policy revision', 'number');
    const remove = document.createElement('button'); remove.type = 'button'; remove.textContent = 'Remove comparison policy';
    const row = {group,id,revision}; rows.push(row);
    remove.addEventListener('click', () => { rows.splice(rows.indexOf(row),1); group.remove(); add.focus(); });
    group.append(remove); list.append(group);
  }
  add.addEventListener('click', addPolicy);
  addPolicy();
  const button = document.createElement('button'); button.type = 'submit'; button.textContent = 'Compare policies';
  form.append(list,add,button);
  const result = document.createElement('section'); result.setAttribute('aria-live','polite');
  const context = document.createElement('p');
  context.textContent = 'Simulation baseline: configured scenario. Live mission: current rescue run; comparison does not change its mission records.';
  root.append(context,form,result);
  let selection = workspace.getSnapshot().selectionVersion;
  workspace.subscribe((state) => {if (selection !== state.selectionVersion) {selection=state.selectionVersion;result.replaceChildren();}});
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (button.disabled) return;
    result.replaceChildren();
    if (!scenarioId.value.trim()) return showError(result,'A configured scenario is required before comparison.');
    const policyKeys = rows.filter((row) => row.id.value.trim()).map((row) => [row.id.value,Number(row.revision.value)]);
    if (!policyKeys.length) return showError(result,'A configured policy is required before comparison.');
    button.disabled = true;
    const version = workspace.getSnapshot().selectionVersion;
    try {
      const answer = await workspace.invoke('compare',{command:{scenario_id:scenarioId.value,scenario_revision:Number(revision.value),policy_keys:policyKeys}});
      if (version !== workspace.getSnapshot().selectionVersion) return;
      outcomes.render(answer,{operation:'compare',label:'Simulation comparison',target:result});
      for (const snapshot of Array.isArray(answer?.value) ? answer.value : []) renderRun(result,snapshot);
    } catch (error) { if (version === workspace.getSnapshot().selectionVersion) showError(result,error.message); }
    finally { button.disabled = false; }
  });
}

function field(parent,labelText,type='text') {
  const label = document.createElement('label'); label.textContent = labelText;
  const input = document.createElement('input'); input.type = type;
  input.setAttribute('aria-label',labelText);
  if (type === 'number') {input.min='1';input.step='1';input.value='1'; input.required=true;}
  label.append(input);parent.append(label);return input;
}

function showError(target,message) {
  const alert = document.createElement('p'); alert.setAttribute('role','alert');alert.textContent=message;target.replaceChildren(alert);
}


function renderRun(parent,snapshot) {
  const section = document.createElement('article');
  const heading = document.createElement('h4');
  heading.textContent = `Policy ${snapshot.run.policy_id} · scenario ${snapshot.run.scenario_id} · ${snapshot.run.status}`;
  const identity = document.createElement('p'); identity.textContent = `Run ${snapshot.run.run_id}`;
  const timelineHeading = document.createElement('h5'); timelineHeading.textContent = 'Recorded mission timeline';
  const list = document.createElement('ol');
  for (const mission of snapshot.missions ?? []) {
    for (const event of mission.history ?? []) {
      const item = document.createElement('li');
      item.textContent = `t=${event.recorded_at} · ${mission.mission_id} · ${event.action} · confirmed change ${event.confirmed_seats_delta}, pending change ${event.pending_seats_delta} · ${event.reason}`;
      list.append(item);
    }
  }
  if (!list.children.length) {const item=document.createElement('li');item.textContent='No mission transitions were recorded.';list.append(item);}
  section.append(heading,identity,timelineHeading,list);
  parent.append(section);
}
