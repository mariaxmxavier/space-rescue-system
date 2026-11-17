import { createForms } from '../../shared/ui/controls.js';

/** Expose explicit synchronisation and retained-report replay controls.
 * When Communication mounts, typed sequence fields let operators recover
 * protocol state without repeating accepted business operations.
 */
export function registerCommunicationRecovery({root,workspace,outcomes}) {
  const forms = createForms({root,workspace,outcomes});
  const base = [{name:'session_id',label:'Session ID',required:true},{name:'version',label:'Version',type:'number',min:1,required:true}];
  forms.commandForm({operation:'synchronise_inbound',title:'Synchronise inbound',fields:[...base,{name:'next_sequence',label:'Next sequence',type:'number',min:1,required:true}]});
  forms.commandForm({operation:'recover_reports',title:'Recover reports',fields:[...base,{name:'from_sequence',label:'From sequence',type:'number',min:1,required:true},{name:'count',label:'Count',type:'number',min:1,required:true}]});
}
