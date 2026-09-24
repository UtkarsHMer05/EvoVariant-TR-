/**
 * API route: batch variant submission.
 *
 * POST /api/batch/submit — submits a batch of variants for scoring.
 */
import type { NextRequest } from "next/server";
import { configuredScorerUrl, serviceEndpoint } from "~/lib/scorer-endpoint";

export async function POST(request: NextRequest) {
  try {
    const body: unknown = await request.json();
    const configuredUrl = configuredScorerUrl();
    if (!configuredUrl) {
      return Response.json(
        { error: "No research scoring service is configured" },
        { status: 503 },
      );
    }
    const baseUrl = serviceEndpoint(configuredUrl, "/batch/submit");

    const response = await fetch(baseUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const data: unknown = await response.json();
    return Response.json(data, { status: response.status });
  } catch (error) {
    console.error("Batch submit error:", error);
    return Response.json({ error: "Failed to submit batch" }, { status: 500 });
  }
}
