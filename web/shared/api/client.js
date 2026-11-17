/**
 * What: creates the browser transport for one API origin.
 * When called: the application shell starts and feature forms call the returned methods.
 * Why: HTTP details and JSON encoding stay at the outer boundary.
 */
export function createApiClient(origin = globalThis.SPACE_RESCUE_API_ORIGIN || "http://127.0.0.1:8000") {
  const base = origin.replace(/\/$/, "");

  async function request(path, options) {
    let response;
    try {
      response = await fetch(`${base}${path}`, options);
    } catch (cause) {
      throw new Error("The rescue API could not be reached. The result may be uncertain.", { cause });
    }
    let result;
    try {
      result = await response.json();
    } catch (cause) {
      throw new Error("The rescue API returned an unreadable response.", { cause });
    }
    if (!response.ok) {
      const message = typeof result?.detail === "string" ? result.detail : `HTTP ${response.status}`;
      throw new Error(message);
    }
    return result;
  }

  const post = (path, body) => request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  return Object.freeze({
    createRun: (input) => post("/runs", input),
    invoke: (runId, operation, payload) => post(
      `/runs/${encodeURIComponent(runId)}/operations/${encodeURIComponent(operation)}`,
      payload,
    ),
    readState: (runId) => request(`/runs/${encodeURIComponent(runId)}/state`),
    readHistory: (runId) => request(`/runs/${encodeURIComponent(runId)}/history`),
  });
}
