// Simple in-memory sliding-window rate limiter. node-room runs a single web
// instance, so this is enough to cap cost on the open facilitator endpoints
// (see GitHub #6). It resets on redeploy and is not shared across instances;
// when proper auth lands, per-user limits should replace this.
const hits = new Map<string, number[]>();

/** Returns true if the action is allowed (and records it), false if over the limit. */
export function rateLimit(key: string, max: number, windowMs: number): boolean {
  const now = Date.now();
  const recent = (hits.get(key) ?? []).filter((t) => now - t < windowMs);
  if (recent.length >= max) {
    hits.set(key, recent);
    return false;
  }
  recent.push(now);
  hits.set(key, recent);
  return true;
}
