import { env } from "~/env";

/**
 * Resolve the configured research-scoring service.
 *
 * `EVOVARIANT_SCORER_URL` is the preferred server-only variable. The legacy
 * `NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL` is still honoured because
 * existing deployments bake it at build time. Returns null when neither is
 * configured so routes can answer 503 instead of failing with a 500.
 */
export function configuredScorerUrl(): string | null {
  return (
    env.EVOVARIANT_SCORER_URL ??
    env.NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL ??
    null
  );
}

function trimmed(raw: string): string {
  return raw.trim().replace(/\/+$/, "");
}

/** Modal serves one function per hostname, so its endpoint is the root path. */
function isModalFunctionEndpoint(url: string): boolean {
  return /^https?:\/\/[^/]+\.modal\.run$/i.test(url);
}

/**
 * Build the single-variant scoring URL.
 *
 * Accepts either a REST base (`https://host`) or an explicit endpoint
 * (`https://host/score/variant`, or a Modal function hostname) so the same
 * configuration works for the local FastAPI service and Modal deployments.
 */
export function scoreEndpoint(raw: string): string {
  const base = trimmed(raw);
  if (isModalFunctionEndpoint(base) || /\/score\/variant$/i.test(base)) {
    return base;
  }
  return `${base}/score/variant`;
}

/**
 * Build a REST path on the configured service.
 *
 * Batch and result routes require a service that exposes the REST paths from
 * `evovariant_tr.api`; a Modal per-function hostname cannot serve them.
 */
export function serviceEndpoint(raw: string, path: string): string {
  const base = trimmed(raw).replace(/\/score\/variant$/i, "");
  const suffix = path.startsWith("/") ? path : `/${path}`;
  return `${base}${suffix}`;
}
