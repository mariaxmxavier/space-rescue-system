import { createTimeline } from "./timeline.js";
import { renderSnapshot } from "./snapshot.js";
import { renderTechnical } from "./technical.js";

/**
 * What: mounts the case catalogue and an authoritative recorded mission viewer.
 * When called: the application shell starts.
 * Why: selecting one case is sufficient to inspect every point in its execution.
 */
export function registerSimulationViewer({ root, api }) {
  const doc = root.ownerDocument;
  const prefix = `simulation-${crypto.randomUUID()}`;
  root.classList.add("simulation-viewer");
  root.setAttribute("aria-label", "Simulation viewer");
  root.innerHTML = `
    <section class="sim-intro" aria-labelledby="${prefix}-heading">
      <div><p class="sim-eyebrow">SPACE RESCUE / SIMULATIONS</p><h2 id="${prefix}-heading">Every mission. Every decision.</h2><p class="sim-intro-copy">Choose a rescue case and explore the system as it runs. Pause, replay, or jump to any moment.</p></div>
      <div class="sim-case-field"><label for="${prefix}-case">Rescue case</label><select id="${prefix}-case" data-control="case" disabled><option>Loading cases…</option></select><p data-view="description" class="sim-helper"></p></div>
    </section>
    <div class="sim-notification"><p data-view="status" aria-live="polite" aria-atomic="true">Loading simulation cases…</p><p data-view="error" role="alert" hidden></p><button type="button" class="sim-secondary" data-control="retry" hidden>Retry case</button></div>
    <section data-view="recording" hidden>
      <div class="sim-run-bar"><div><span class="sim-badge" data-view="playback-state">Paused</span><span class="sim-run-caption">Recorded execution</span></div><span data-view="run-id" class="sim-run-id"></span></div>
      <section class="sim-timeline" aria-labelledby="${prefix}-timeline-heading">
        <div class="sim-timeline-title"><div><p class="sim-eyebrow">MISSION CLOCK</p><h3 id="${prefix}-timeline-heading">Explore the timeline</h3></div><p class="sim-clock"><span data-view="clock">0</span><span class="sim-helper"> / <span data-view="duration">0</span> logical seconds</span></p></div>
        <label class="sim-sr-only" for="${prefix}-range">Simulation timeline</label><input id="${prefix}-range" data-control="range" type="range" min="0" max="1" value="0" step="any">
        <div class="sim-timeline-controls"><div class="sim-playback-buttons"><button type="button" data-control="play" aria-label="Play simulation">${icon("play")}<span>Play</span></button><button type="button" class="sim-secondary" data-control="previous" aria-label="Previous event">${icon("previous")}<span>Previous</span></button><button type="button" class="sim-secondary" data-control="next" aria-label="Next event"><span>Next</span>${icon("next")}</button><button type="button" class="sim-secondary sim-icon-button" data-control="reset" aria-label="Reset to beginning">${icon("reset")}</button></div><div class="sim-clock-inputs"><div><label for="${prefix}-time">Logical time</label><input id="${prefix}-time" data-control="time" type="number" min="0" step="any" value="0"></div><div><label for="${prefix}-speed">Playback speed</label><select id="${prefix}-speed" data-control="speed"><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="2">2×</option><option value="4">4×</option></select></div></div></div>
        <p class="sim-helper" data-view="snapshot-time"></p>
      </section>
      <div class="sim-view-tabs" role="tablist" aria-label="Simulation view"><button type="button" role="tab" id="${prefix}-overview-tab" aria-controls="${prefix}-overview" aria-selected="true" data-control="overview-tab">Overview</button><button type="button" role="tab" id="${prefix}-technical-tab" aria-controls="${prefix}-technical" aria-selected="false" tabindex="-1" data-control="technical-tab">Technical</button></div>
      <section id="${prefix}-technical" role="tabpanel" aria-labelledby="${prefix}-technical-tab" data-view="technical" hidden></section>
      <div id="${prefix}-overview" role="tabpanel" aria-labelledby="${prefix}-overview-tab" class="sim-workspace"><div class="sim-primary"><section data-view="mission" aria-label="Mission progress"></section><section data-view="fleet" class="sim-panel" aria-label="Fleet at selected time"></section><section data-view="requests" class="sim-panel" aria-label="Requests at selected time"></section><section data-view="decisions" class="sim-panel" aria-label="Decisions at selected time"></section><section data-view="communication" class="sim-panel" aria-label="Communication at selected time"></section><section data-view="other" class="sim-panel" aria-label="Market and experiments at selected time"></section><section class="sim-panel"><details data-view="complete-details"><summary>Complete committed state</summary><p class="sim-helper">All returned fields from the selected snapshot. Historical state is separate from the advanced live workspace.</p><pre data-view="complete-state"></pre></details></section></div><aside class="sim-event-column"><section class="sim-panel sim-event-focus" aria-labelledby="${prefix}-event-heading"><p class="sim-eyebrow">SELECTED MOMENT</p><h3 id="${prefix}-event-heading" data-view="event-title">Mission prepared</h3><div data-view="event-outcomes"></div><details><summary>Complete event and outcomes</summary><pre data-view="event-raw"></pre></details></section><section class="sim-panel sim-evidence-panel"><h3>Case verification</h3><div data-view="evidence"></div></section><section class="sim-panel sim-events-panel" aria-labelledby="${prefix}-events-heading"><h3 id="${prefix}-events-heading">Mission events</h3><p class="sim-helper">Select any event, including separate actions at the same time.</p><ol data-view="events" class="sim-events"></ol></section></aside></div>
    </section>`;
  const control = (name) => root.querySelector(`[data-control="${name}"]`);
  const view = (name) => root.querySelector(`[data-view="${name}"]`);
  let catalogue = [];
  let transcript = null;
  let timeline = null;
  let generation = 0;
  let timer = null;
  let disposed = false;
  let listFailed = false;
  let selectedMission = null;

  function pause() {
    clearTimeout(timer);
    timer = null;
    control("play").setAttribute("aria-label", "Play simulation");
    control("play").innerHTML = `${icon("play")}<span>Play</span>`;
    view("playback-state").textContent = "Paused";
    view("playback-state").classList.remove("is-playing");
  }

  function render() {
    if (!timeline || !transcript) return;
    const current = timeline.snapshot();
    const frame = current.frame;
    const caseInfo = catalogue.find((item) => item.id === transcript.case_id);
    view("clock").textContent = formatTime(current.time);
    view("duration").textContent = formatTime(current.duration);
    control("range").max = String(current.duration || 1);
    control("range").value = String(current.time);
    control("range").setAttribute("aria-valuetext", `Time ${formatTime(current.time)} of ${formatTime(current.duration)} logical seconds`);
    control("range").disabled = current.duration === 0;
    control("time").max = String(current.duration);
    control("time").value = String(current.time);
    control("previous").disabled = current.index === -1;
    control("next").disabled = current.atEnd;
    control("play").disabled = transcript.frames.length === 0;
    const committedTime = formatTime(frame.logical_time || 0);
    view("snapshot-time").textContent = `Showing state committed at t=${committedTime}${Number(frame.logical_time) !== current.time ? ` · No intervening event before t=${formatTime(current.time)}.` : current.index < 0 ? " · Before the first event. Press Play or Next to begin." : ` · Event ${current.index + 1} of ${transcript.frames.length}.`}`;
    renderSnapshot({ root, state: frame.state, progress: frame.progress, missionProgress: frame.mission_progress, missionId: selectedMission || transcript.mission_id, onMissionSelect: (id) => { selectedMission = id; render(); root.querySelector('[aria-label="Inspect mission"]')?.focus(); } });
    renderTechnical(view("technical"), transcript, current.index);
    view("event-title").textContent = current.index < 0 ? "Mission prepared" : frame.label || humanize(frame.event_id);
    view("event-raw").textContent = JSON.stringify({ event_id: current.index < 0 ? "initial-setup" : frame.event_id, ordinal: frame.ordinal, logical_time: frame.logical_time, action: frame.action, outcomes: frame.outcomes, progress: frame.progress, evidence: frame.evidence }, null, 2);
    view("event-outcomes").replaceChildren();
    if (current.index < 0) {
      appendText(view("event-outcomes"), "p", "The mission and fleet are registered. No timeline event has been played yet.", "sim-helper");
      if (frame.outcomes?.length) appendText(view("event-outcomes"), "p", `Setup recorded ${frame.outcomes.length} API calls. Expand the complete event to inspect every input and outcome.`, "sim-helper");
    } else {
      const actionOutcomes = (frame.outcomes || []).filter((outcome) => !["get_progress", "get_session", "get_deliveries"].includes(outcome.operation));
      for (const outcome of actionOutcomes) {
        const answer = outcome.result || outcome;
        const status = answer.status || answer.application_status || (outcome.http_status ? `HTTP ${outcome.http_status}` : "Recorded outcome");
        appendText(view("event-outcomes"), "p", `${outcome.operation ? `${humanize(outcome.operation)} · ` : ""}${humanize(status)}${answer.reason ? ` · ${answer.reason}` : ""}`, "sim-outcome");
      }
    }
    const matched = new Set(transcript.frames.slice(0, current.index + 1).flatMap((item) => (item.evidence || []).filter((evidence) => evidence.matched).map((evidence) => evidence.situation_id)));
    const evidenceRoot = view("evidence");
    evidenceRoot.replaceChildren();
    appendText(evidenceRoot, "p", `${matched.size} / ${caseInfo?.situation_count ?? transcript.result.matched_situations?.length ?? 0} situations observed`, "sim-evidence-count");
    if (current.atEnd) {
      appendText(evidenceRoot, "p", transcript.result.passed ? "Case passed" : "Case failed", transcript.result.passed ? "sim-verification-pass" : "sim-verification-fail");
      if (transcript.result.failure_detail) appendText(evidenceRoot, "p", transcript.result.failure_detail, "sim-helper");
      const complete = doc.createElement("details");
      appendText(complete, "summary", "Complete verification result");
      appendText(complete, "pre", JSON.stringify(transcript.result, null, 2));
      evidenceRoot.append(complete);
    } else appendText(evidenceRoot, "p", "Verification follows all events, including deliveries after mission completion.", "sim-helper");
    for (const situation of matched) appendText(evidenceRoot, "span", humanize(situation), "sim-evidence-tag");
    for (const button of view("events").querySelectorAll("button")) {
      const index = Number(button.dataset.index);
      button.setAttribute("aria-current", index === current.index ? "step" : "false");
      button.classList.toggle("is-past", index < current.index);
      button.querySelector(".sim-event-position").textContent = index === current.index ? "Selected" : index < current.index ? "Recorded" : "Upcoming";
    }
    if (current.atEnd && timer !== null) pause();
  }

  function selectView(name) {
    for (const candidate of ['overview', 'technical']) {
      const active = candidate === name;
      const button = control(`${candidate}-tab`);
      button.setAttribute('aria-selected', String(active));
      button.tabIndex = active ? 0 : -1;
      root.querySelector(`#${prefix}-${candidate}`).hidden = !active;
    }
  }
  for (const name of ['overview', 'technical']) {
    const button = control(`${name}-tab`);
    button.addEventListener('click', () => selectView(name));
    button.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
        event.preventDefault();
        const other = name === 'overview' ? 'technical' : 'overview';
        selectView(other);
        control(`${other}-tab`).focus();
      }
    });
  }

  function schedule() {
    timer = setTimeout(() => {
      if (!timeline || disposed) return;
      timeline.next();
      render();
      if (timer !== null && !timeline.snapshot().atEnd) schedule();
    }, 1200 / Number(control("speed").value));
  }

  function seek(value) { pause(); timeline?.seek(value); render(); }
  control("range").addEventListener("input", (event) => seek(event.target.value));
  control("time").addEventListener("change", (event) => seek(event.target.value));
  control("time").addEventListener("keydown", (event) => { if (event.key === "Enter") { event.preventDefault(); seek(event.target.value); } });
  control("previous").addEventListener("click", () => { pause(); timeline?.previous(); render(); });
  control("next").addEventListener("click", () => { pause(); timeline?.next(); render(); });
  control("reset").addEventListener("click", () => { pause(); timeline?.reset(); render(); });
  control("play").addEventListener("click", () => {
    if (!timeline) return;
    if (timer !== null) { pause(); return; }
    if (timeline.snapshot().atEnd) timeline.reset();
    control("play").setAttribute("aria-label", "Pause simulation");
    control("play").innerHTML = `${icon("pause")}<span>Pause</span>`;
    view("playback-state").textContent = "Playing";
    view("playback-state").classList.add("is-playing");
    render();
    schedule();
  });
  control("speed").addEventListener("change", () => { if (timer !== null) { clearTimeout(timer); schedule(); } });
  control("case").addEventListener("change", () => { void prepare(control("case").value); });
  control("retry").addEventListener("click", () => { if (listFailed) void loadCatalogue(); else void prepare(control("case").value); });
  // Background tabs pause instead of letting a hidden recording race ahead.
  const visibility = () => { if (doc.hidden) pause(); };
  doc.addEventListener("visibilitychange", visibility);

  function showError(error) {
    view("status").textContent = "Simulation could not be prepared.";
    view("error").textContent = `${error.message || "The simulation is unavailable."} Retry this case when the API is available.`;
    view("error").hidden = false;
    control("retry").hidden = false;
  }

  async function prepare(caseId) {
    pause();
    const requestGeneration = ++generation;
    transcript = null;
    timeline = null;
    selectedMission = null;
    root.setAttribute("aria-busy", "true");
    view("recording").hidden = true;
    for (const name of ["mission", "fleet", "requests", "decisions", "communication", "other", "events", "evidence", "event-outcomes"]) view(name).replaceChildren();
    view("complete-state").textContent = "";
    view("event-raw").textContent = "";
    view("error").hidden = true;
    control("retry").hidden = true;
    const selected = catalogue.find((item) => item.id === caseId);
    view("description").textContent = selected?.description || "";
    view("status").textContent = `Preparing ${selected?.name || caseId} through the rescue API…`;
    try {
      const recording = await api.runSimulationCase(caseId);
      if (disposed || requestGeneration !== generation) return;
      if (recording.case_id !== caseId || !recording.result) throw new Error("The API returned a recording for a different or incomplete case.");
      timeline = createTimeline(recording);
      transcript = recording;
      view("run-id").textContent = recording.run_id;
      view("status").textContent = `${selected?.name || caseId} is ready. Paused at the beginning.`;
      view("recording").hidden = false;
      if (!recording.result.passed) {
        view("status").textContent = "Recording available with an execution failure. Paused at the beginning.";
        view("error").textContent = `Case execution failed: ${recording.result.failure_detail || "Not all required evidence or final-state expectations passed."} You can inspect the recorded events or retry the case.`;
        view("error").hidden = false;
        control("retry").hidden = false;
      }
      renderEvents();
      render();
      try {
        const url = new URL(globalThis.location.href);
        url.searchParams.set("case", caseId);
        globalThis.history?.replaceState(null, "", url);
      } catch { /* Embedded viewers need not own their surrounding URL. */ }
    } catch (error) {
      if (!disposed && requestGeneration === generation) showError(error);
    } finally {
      if (requestGeneration === generation) root.removeAttribute("aria-busy");
    }
  }

  function renderEvents() {
    const list = view("events");
    list.replaceChildren();
    const entries = [{ logical_time: transcript.initial.logical_time, label: "Mission prepared" }, ...transcript.frames];
    entries.forEach((frame, offset) => {
      const index = offset - 1;
      const item = doc.createElement("li");
      const button = doc.createElement("button");
      button.type = "button";
      button.dataset.index = String(index);
      appendText(button, "span", `t=${formatTime(frame.logical_time || 0)}`, "sim-event-time");
      const body = doc.createElement("span");
      appendText(body, "strong", frame.label || humanize(frame.event_id));
      appendText(body, "span", "Upcoming", "sim-event-position");
      button.append(body);
      button.addEventListener("click", () => { pause(); timeline.select(index); render(); });
      item.append(button);
      list.append(item);
    });
  }

  async function loadCatalogue() {
    listFailed = false;
    view("error").hidden = true;
    control("retry").hidden = true;
    try {
      const response = await api.listSimulationCases();
      if (disposed) return;
      if (!Array.isArray(response.cases)) throw new Error("The API returned an unreadable case catalogue.");
      catalogue = response.cases;
      control("case").replaceChildren(...catalogue.map((item) => {
        const option = doc.createElement("option");
        option.value = item.id;
        option.textContent = `${item.name} · ${item.situation_count} ${item.situation_count === 1 ? "situation" : "situations"}`;
        return option;
      }));
      if (!catalogue.length) {
        view("status").textContent = "No simulation cases are available. The advanced workspace remains available below.";
        return;
      }
      control("case").disabled = false;
      const requestedCase = new URL(globalThis.location.href).searchParams.get("case");
      const selected = catalogue.find((item) => item.id === requestedCase) || catalogue.find((item) => item.id === "baseline") || catalogue[0];
      control("case").value = selected.id;
      await prepare(selected.id);
    } catch (error) { if (!disposed) { listFailed = true; showError(error); } }
  }

  void loadCatalogue();
  return () => { disposed = true; generation += 1; pause(); doc.removeEventListener("visibilitychange", visibility); root.replaceChildren(); };
}

/** What: formats exact recorded instants for labels. When: the clock renders. Why: logical seconds remain distinct from wall-clock playback. */
function formatTime(value) { return new Intl.NumberFormat("en", { maximumFractionDigits: 6 }).format(Number(value)); }
function humanize(value) { return String(value || "").replace(/_/g, " ").replace(/^./, (character) => character.toUpperCase()); }
function appendText(parent, tag, text, className) { const element = parent.ownerDocument.createElement(tag); element.textContent = text; if (className) element.className = className; parent.append(element); return element; }
function icon(name) {
  const paths = { play: '<path d="m8 5 11 7-11 7Z"/>', pause: '<path d="M8 5v14M16 5v14"/>', previous: '<path d="m15 5-7 7 7 7"/>', next: '<path d="m9 5 7 7-7 7"/>', reset: '<path d="M3 10a9 9 0 1 1 2 8M3 4v6h6"/>' };
  return `<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${paths[name]}</svg>`;
}
