/** Render recorded API exchanges grouped by the capability each operation concerns. */
const groups = [
  ['Mission center', ['create_run', 'read_state', 'get_state', 'state', 'register_mission', 'get_progress', 'get_history', 'create_request', 'cancel_request', 'expire_request']],
  ['B3 Market', ['publish_availability', 'publish_offer', 'request_quotes', 'record_quote', 'accept_quote', 'reject_quote', 'expire_quotes']],
  ['Mobilisation', ['mobilise', 'get_decision', 'compare']],
  ['Communication', ['record_response', 'get_session', 'get_deliveries', 'synchronise_inbound', 'recover_reports']],
  ['Fleet', ['register_ship']],
];

function groupFor(operation) {
  return groups.find(([, operations]) => operations.includes(operation))?.[0] || 'Other operations';
}

function el(doc, tag, text, className) {
  const node = doc.createElement(tag);
  if (text !== undefined) node.textContent = String(text);
  if (className) node.className = className;
  return node;
}

/** Show only exchanges captured up to the selected timeline position. */
export function renderTechnical(root, transcript, index) {
  const doc = root.ownerDocument;
  const frames = [transcript.initial, ...transcript.frames.slice(0, index + 1)];
  const entries = frames.flatMap((frame) => (frame.outcomes || []).map((call) => ({call, time: frame.logical_time, event: frame.label || frame.event_id || 'Setup'})));
  root.replaceChildren();
  const intro = el(doc, 'div', undefined, 'tech-intro');
  intro.append(el(doc, 'p', 'SYSTEM ACTIVITY', 'sim-eyebrow'), el(doc, 'h3', 'Technical view'), el(doc, 'p', 'Recorded API inputs and outputs through the selected moment. Operations are grouped by the capability they concern; internal calls between components are not traced.', 'sim-helper'));
  root.append(intro);
  const visual = el(doc, 'div', undefined, 'tech-components');
  visual.setAttribute('aria-label', 'Recorded activity by component');
  for (const [name] of groups) {
    const relevant = entries.filter(({call}) => groupFor(call.operation) === name);
    const card = el(doc, 'article', undefined, 'tech-component');
    card.append(el(doc, 'h4', name), el(doc, 'p', `Input → ${name} → Output`, 'tech-flow'), el(doc, 'strong', String(relevant.length)), el(doc, 'span', relevant.length === 1 ? 'recorded exchange' : 'recorded exchanges'));
    if (relevant.length) {
      const last = relevant.at(-1).call;
      card.append(el(doc, 'p', `Latest: ${String(last.operation).replaceAll('_', ' ')}`, 'sim-helper'));
    } else card.append(el(doc, 'p', 'No recorded exchanges yet.', 'sim-helper'));
    visual.append(card);
  }
  root.append(visual);
  const heading = el(doc, 'div', undefined, 'tech-log-heading');
  heading.append(el(doc, 'h3', 'Exchange log'), el(doc, 'p', `${entries.length} recorded calls through this moment`, 'sim-helper'));
  root.append(heading);
  if (!entries.length) root.append(el(doc, 'p', 'No API exchanges recorded at this moment.', 'sim-empty'));
  const list = el(doc, 'ol', undefined, 'tech-log');
  for (const {call, time, event} of entries) {
    const item = el(doc, 'li');
    const details = el(doc, 'details');
    const summary = el(doc, 'summary');
    const answer = call.result || {};
    summary.append(el(doc, 'span', `t=${time ?? '0'}`, 'tech-time'), el(doc, 'strong', String(call.operation || 'Recorded call').replaceAll('_', ' ')), el(doc, 'span', groupFor(call.operation), 'tech-group'), el(doc, 'span', `${answer.status || 'response'} · HTTP ${call.http_status ?? '—'}${answer.reason ? ` · ${answer.reason}` : ''}`, 'tech-status'));
    details.append(summary, el(doc, 'p', `Event: ${event}`, 'sim-helper'));
    const data = el(doc, 'div', undefined, 'tech-io');
    for (const [title, value] of [['Input', call.input], ['Output', call.result]]) {
      const block = el(doc, 'section');
      block.append(el(doc, 'h4', title), el(doc, 'pre', JSON.stringify(value ?? null, null, 2)));
      data.append(block);
    }
    details.append(data); item.append(details); list.append(item);
  }
  root.append(list);
}
