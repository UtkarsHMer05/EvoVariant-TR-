/**
 * API route: return protocol/version info.
 *
 * GET /api/protocol — returns the frozen protocol version.
 */
import type { NextRequest } from "next/server";

export async function GET(_request: NextRequest) {
  return Response.json({
    protocol_version: "1.0.0",
    ml_extension_protocol_version: "1.0.0",
    frozen_at: "2026-08-18",
    identity: "evovariant-tr",
    context_length_bp: 8192,
    research_only: true,
    classification_logic: "server-side registered research artifacts only",
  });
}
