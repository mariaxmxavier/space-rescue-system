import { createForms } from '../../shared/ui/controls.js';

/** Inspect complete delivery classifications and authoritative session counters.
 * When Communication opens, reads preserve every returned field and never
 * reconstruct message ordering or seat effects in the browser.
 */
export function registerCommunicationInspection({root,workspace,outcomes}) {
  const forms = createForms({root,workspace,outcomes});
  forms.scalarForm({operation:'get_deliveries',title:'Inspect deliveries',fields:[{name:'message_id',label:'Message ID',required:true}]});
  forms.scalarForm({operation:'get_session',title:'Inspect session',fields:[{name:'session_id',label:'Session ID',required:true}]});
}
