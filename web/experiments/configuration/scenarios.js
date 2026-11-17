import { createValueEditor } from '../../shared/ui/value-editor.js';
import { scenarioSchema } from './schemas.js';

/** Configure immutable policies and complete nested scenarios before run creation.
 * When Experiments mounts, repeatable controls expose every baseline and fault
 * setting without forcing the operator to author JSON.
 */
export function registerScenarioConfiguration({ root }) {
  const policies = [];
  const scenarios = [];
  if (!document.querySelector('link[data-shared-ui]')) {
    const styles = document.createElement('link'); styles.rel='stylesheet'; styles.href='/shared/ui/styles.css'; styles.dataset.sharedUi='true'; document.head.append(styles);
  }
  const notice = document.createElement('p');
  notice.textContent = 'Configure policies and scenario baselines before creating a run. Changes here apply to the next new run.';
  root.append(notice);
  collection(root, 'Add mobilisation policy', policies, makePolicyForm);
  collection(root, 'Add scenario', scenarios, () => {
    const editor = createValueEditor(scenarioSchema, 'Scenario');
    return {form:editor.element, value:editor.value};
  });
  return Object.freeze({ values: () => ({policies:policies.map((item) => item.value()), scenarios:scenarios.map((item) => item.value())}) });
}

function collection(root, title, values, create) {
  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = title;
  const list = document.createElement('div');
  button.addEventListener('click', () => {
    const editor = create();
    const remove = document.createElement('button');
    remove.type = 'button';
    remove.textContent = title.includes('policy') ? 'Remove policy' : 'Remove scenario';
    remove.addEventListener('click', () => { values.splice(values.indexOf(editor),1); editor.form.remove(); button.focus(); });
    editor.form.append(remove);
    values.push(editor);
    list.append(editor.form);
  });
  root.append(button, list);
  return list;
}

function makePolicyForm() {
  const policySchema = {type:'object',fields:[
    {name:'policy_id',schema:{type:'string'}},
    {name:'revision',schema:{type:'integer'},default:1},
    {name:'name',schema:{type:'string'}},
    {name:'selection_criteria',schema:{type:'enum',values:['earliest_arrival','largest_capacity','priority_queue','min_cost_flow','cp_sat','knapsack']}},
  ]};
  const editor = createValueEditor(policySchema, 'Mobilisation policy');
  const criteria = createValueEditor({type:'array',item:{type:'tuple',items:[{type:'string'},{type:'string'}]}},'Additional selection criteria');
  const enabled = document.createElement('input'); enabled.type='checkbox';
  const label = document.createElement('label'); label.append(enabled,document.createTextNode(' Use named criteria pairs'));
  editor.element.append(label,criteria.element);
  criteria.element.hidden=true;
  enabled.addEventListener('change',() => {criteria.element.hidden=!enabled.checked;});
  return {form:editor.element, value:() => {
    const value=editor.value();
    if (enabled.checked) value.selection_criteria=[['strategy',value.selection_criteria],...criteria.value()];
    return value;
  }};
}
