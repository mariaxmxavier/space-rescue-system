/**
 * What: manages the selected run and its latest committed server snapshot.
 * When called: constructed by the shell and used by tabs and capability forms.
 * Why: every view observes the same run and stale asynchronous replies cannot cross runs.
 */
export function createWorkspace(api, storage = globalThis.localStorage) {
  let runId = null;
  let snapshot = null;
  let refreshedAt = null;
  let stale = false;
  let history = null;
  let generation = 0;
  const listeners = new Set();

  const publish = () => {
    const value = getSnapshot();
    for (const listener of listeners) listener(value);
  };
  const getSnapshot = () => Object.freeze({ runId, snapshot, refreshedAt, stale, history });

  async function selectRun(nextRunId) {
    runId = String(nextRunId).trim();
    snapshot = null;
    refreshedAt = null;
    stale = false;
    history = null;
    generation += 1;
    storage?.setItem("space-rescue-run-id", runId);
    publish();
    await refreshState();
  }

  async function createRun(input) {
    const created = await api.createRun(input);
    await selectRun(created.application_run_id);
    return created;
  }

  async function refreshState() {
    if (!runId) return null;
    const requestedRun = runId;
    const requestGeneration = ++generation;
    try {
      const nextSnapshot = await api.readState(requestedRun);
      if (runId !== requestedRun || generation !== requestGeneration) return null;
      snapshot = nextSnapshot;
      refreshedAt = new Date().toISOString();
      stale = false;
    } catch (error) {
      if (runId !== requestedRun || generation !== requestGeneration) return null;
      stale = true;
      publish();
      throw error;
    }
    publish();
    return snapshot;
  }

  async function loadHistory() {
    if (!runId) return null;
    const requestedRun = runId;
    const requestGeneration = generation;
    const nextHistory = await api.readHistory(requestedRun);
    if (runId !== requestedRun || generation !== requestGeneration) return null;
    history = nextHistory;
    publish();
    return history;
  }

  async function invoke(operation, payload) {
    if (!runId) throw new Error("Open or create a run before submitting an operation.");
    const submittedRun = runId;
    const result = await api.invoke(submittedRun, operation, payload);
    if (runId === submittedRun) {
      try { await refreshState(); } catch { /* A committed result remains valid; state is marked stale. */ }
    }
    return result;
  }

  return Object.freeze({
    getSnapshot,
    subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener); },
    selectRun,
    createRun,
    refreshState,
    loadHistory,
    invoke,
  });
}
