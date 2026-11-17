/** Register ship responses with optional session sequencing and lossless timing.
 * When Communication mounts, this form delegates delivery and request finality
 * to the API while preserving the identity of each submitted message.
 */
export function registerResponses({ forms }) {
  forms.commandForm({
    operation: 'record_response',
    title: 'Record response',
    fields: [
      {name:'message_id',label:'Message ID',required:true},
      {name:'delivery_id',label:'Delivery ID',required:true},
      {name:'attempt_number',label:'Attempt number',type:'number',min:1,required:true},
      {name:'request_id',label:'Request ID',required:true},
      {name:'outcome',label:'Outcome',options:['accepted','partially_accepted','refused'],required:true},
      {name:'confirmed_seats',label:'Confirmed seats',type:'number',min:0,required:true},
      {name:'sent_at',label:'Sent at (seconds)',required:true},
      {name:'received_at',label:'Received at (seconds)',optional:true,hint:'Leave empty to let the API derive receipt from communication timing.'},
      {name:'communication_rtt_seconds',label:'Communication round-trip time (seconds)',optional:true},
      {name:'include_envelope',label:'Include session envelope',type:'checkbox'},
      {name:'session_id',label:'Session ID',optional:true},
      {name:'version',label:'Session version',type:'number',min:1,optional:true},
      {name:'direction',label:'Session direction',options:['inbound','outbound']},
      {name:'sequence',label:'Sequence',type:'number',min:1,optional:true},
    ],
    transform: ({command}) => {
      const {include_envelope,session_id,version,direction,sequence,...response} = command;
      if (include_envelope && (!session_id || !version || !sequence)) throw new Error('A session envelope needs Session ID, Session version and Sequence.');
      return {command:{...response, received_at:response.received_at ?? null,
        envelope:include_envelope ? {session_id,version,direction,sequence} : null}};
    },
  });
}
