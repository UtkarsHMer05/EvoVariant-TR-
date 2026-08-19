/**
 * API route: return protocol/version info.
 * 
 * GET /api/protocol — returns the frozen protocol version.
 */
import type { NextRequest } from "next/server";

export async function GET(_request: NextRequest) {
  return Response.json({
    protocol_version: "1.0.0",
    frozen_at: "2026-08-18",
    identity: "evovariant-tr",
  });
}
