/** What: selects recorded simulation snapshots. When: viewer controls seek or step. Why: every panel shares one historical cursor without repeating mutations. */
export function createTimeline(transcript) {
  const frames = transcript.frames;
  if (!transcript.initial?.state || !Array.isArray(frames)) throw new Error("The simulation returned an incomplete recording.");
  let previousTime = -Infinity;
  for (const frame of frames) {
    const time = Number(frame.logical_time);
    if (!Number.isFinite(time) || time < 0 || time < previousTime || !frame.state || !frame.progress) {
      throw new Error("The simulation recording contains an invalid snapshot.");
    }
    previousTime = time;
  }
  let index = -1;
  let time = Number(transcript.initial.logical_time || 0);
  const duration = frames.length ? Number(frames.at(-1).logical_time) : time;
  const snapshot = () => Object.freeze({ index, time, duration, frame: index < 0 ? transcript.initial : frames[index], atEnd: index === frames.length - 1 });
  return Object.freeze({
    snapshot,
    seek(value) {
      const requested = Number(value);
      if (!Number.isFinite(requested)) return snapshot();
      time = Math.max(0, Math.min(duration, requested));
      index = frames.findLastIndex((frame) => Number(frame.logical_time) <= time);
      return snapshot();
    },
    select(value) {
      index = Math.max(-1, Math.min(frames.length - 1, value));
      time = Number((index < 0 ? transcript.initial : frames[index]).logical_time || 0);
      return snapshot();
    },
    reset() { return this.select(-1); },
    next() { return this.select(index + 1); },
    previous() { return this.select(index - 1); },
  });
}
