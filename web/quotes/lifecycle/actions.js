import { createForms } from '../../shared/ui/controls.js';

/** Mount quote solicitation, recording and closure through the public API.
 * When Quotes opens, the shared primitives preserve integer seats and decimal
 * times, and keep temporary capacity holds distinct from confirmed transport.
 */
export function renderQuoteActions({content,workspace,outcomes}) {
  const forms = createForms({root:content,workspace,outcomes});
  const text = (name,label,optional=false) => ({name,label,required:!optional,optional});
  forms.commandForm({operation:'request_quotes',title:'Request quotes',fields:[text('mission_id','Mission ID'),text('now','Current time'),text('response_deadline','Response deadline',true)]});
  forms.commandForm({operation:'record_quote',title:'Record quote',fields:[
    text('offer_id','Offer ID'),text('rfq_id','RFQ ID'),{name:'offered_seats',label:'Offered seats',type:'number',min:1,required:true},
    text('arrival_estimate_seconds','Arrival estimate'),text('expires_at','Expires at'),text('recorded_at','Recorded at'),
    {name:'status',label:'Quote status',options:['held','accepted','rejected','expired']},
    text('request_id','Associated request ID',true),text('now','Current time'),
  ],transform:({command:{now,...offer}}) => ({command:{offer,now}})});
  forms.commandForm({operation:'accept_quote',title:'Accept quote',fields:[text('command_id','Command ID'),text('mission_id','Mission ID'),text('quote_id','Quote ID'),text('now','Current time'),text('response_deadline','Response deadline',true),text('decision_id','Decision ID',true),text('revision_id','Revision ID',true)]});
  forms.commandForm({operation:'reject_quote',title:'Reject quote',fields:[text('quote_id','Quote ID'),text('now','Current time')]});
  forms.scalarForm({operation:'expire_quotes',title:'Expire quotes',fields:[text('now','Current time')]});
}
