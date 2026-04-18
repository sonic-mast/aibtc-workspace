/**
 * State API Worker — authenticated KV-backed state store for an AIBTC agent.
 *
 * Endpoints (all require `Authorization: Bearer ${STATE_API_TOKEN}`):
 *   GET    /state                  — return the full state object
 *   PUT    /state                  — replace the full state object (body is JSON)
 *   PATCH  /state                  — shallow-merge partial state (body is JSON)
 *   GET    /kv/:key                — read a single KV key (returns JSON)
 *   PUT    /kv/:key                — write a single KV key (body is JSON)
 *   DELETE /kv/:key                — delete a single KV key
 *   POST   /kv/:key/append         — atomic array append (body is any JSON value; pushed onto existing array; creates [] if missing)
 *   GET    /keys                   — list all keys (?prefix=foo optional)
 *   GET    /health                 — no auth, returns ok
 *
 * Bindings:
 *   STATE_KV         — Workers KV namespace holding all state
 *   STATE_API_TOKEN  — secret bearer token for auth
 *
 * The primary state blob lives under the KV key "state". Other keys (e.g.
 * daily run logs, pending signals, cached derived data) live under arbitrary
 * keys in the same namespace. The `/state` endpoints are a thin convenience
 * wrapper around `/kv/state`.
 */

const STATE_KEY = "state";

function ok(body, init = {}) {
  return new Response(
    typeof body === "string" ? body : JSON.stringify(body),
    {
      status: init.status ?? 200,
      headers: {
        "Content-Type": init.contentType ?? "application/json",
        ...(init.headers ?? {}),
      },
    }
  );
}

function err(status, message) {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function requireAuth(request, env) {
  const expected = env.STATE_API_TOKEN;
  if (!expected) return err(500, "STATE_API_TOKEN not configured");
  const header = request.headers.get("Authorization") || "";
  const token = header.startsWith("Bearer ") ? header.slice(7) : "";
  if (token !== expected) return err(401, "unauthorized");
  return null;
}

async function readJson(request) {
  try {
    const text = await request.text();
    if (!text) return undefined;
    return JSON.parse(text);
  } catch {
    return null; // caller distinguishes parse-fail vs empty
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";
    const method = request.method.toUpperCase();

    // Public health check
    if (path === "/health" && method === "GET") {
      return ok({ ok: true, ts: new Date().toISOString() });
    }

    // Everything else requires bearer auth
    const authError = requireAuth(request, env);
    if (authError) return authError;

    // /state — shortcut for /kv/state
    if (path === "/state") {
      if (method === "GET") {
        const current = await env.STATE_KV.get(STATE_KEY, "json");
        return ok(current ?? {});
      }
      if (method === "PUT") {
        const body = await readJson(request);
        if (body === null) return err(400, "invalid JSON body");
        await env.STATE_KV.put(STATE_KEY, JSON.stringify(body ?? {}));
        return ok({ ok: true, key: STATE_KEY });
      }
      if (method === "PATCH") {
        const patch = await readJson(request);
        if (patch === null || typeof patch !== "object" || Array.isArray(patch)) {
          return err(400, "PATCH body must be a JSON object");
        }
        const current = (await env.STATE_KV.get(STATE_KEY, "json")) ?? {};
        const merged = { ...current, ...patch };
        await env.STATE_KV.put(STATE_KEY, JSON.stringify(merged));
        return ok(merged);
      }
      return err(405, `method ${method} not allowed on /state`);
    }

    // /kv/:key — single-key operations
    const kvMatch = path.match(/^\/kv\/([^/]+)(\/append)?$/);
    if (kvMatch) {
      const key = decodeURIComponent(kvMatch[1]);
      const isAppend = !!kvMatch[2];

      if (isAppend) {
        if (method !== "POST") return err(405, "append requires POST");
        const entry = await readJson(request);
        if (entry === null) return err(400, "invalid JSON body");
        const existing = (await env.STATE_KV.get(key, "json")) ?? [];
        if (!Array.isArray(existing)) {
          return err(409, `key "${key}" is not an array`);
        }
        existing.push(entry);
        await env.STATE_KV.put(key, JSON.stringify(existing));
        return ok({ ok: true, key, length: existing.length });
      }

      if (method === "GET") {
        const value = await env.STATE_KV.get(key, "json");
        if (value === null) return err(404, `key "${key}" not found`);
        return ok(value);
      }
      if (method === "PUT") {
        const body = await readJson(request);
        if (body === null) return err(400, "invalid JSON body");
        await env.STATE_KV.put(key, JSON.stringify(body));
        return ok({ ok: true, key });
      }
      if (method === "DELETE") {
        await env.STATE_KV.delete(key);
        return ok({ ok: true, key });
      }
      return err(405, `method ${method} not allowed on /kv/:key`);
    }

    // /keys — list all keys (paginated)
    if (path === "/keys" && method === "GET") {
      const prefix = url.searchParams.get("prefix") ?? undefined;
      const limit = Math.min(
        parseInt(url.searchParams.get("limit") ?? "1000", 10) || 1000,
        1000
      );
      const listed = await env.STATE_KV.list({ prefix, limit });
      return ok({
        keys: listed.keys.map((k) => k.name),
        list_complete: listed.list_complete,
        cursor: listed.cursor ?? null,
      });
    }

    return err(404, `no route for ${method} ${path}`);
  },
};
