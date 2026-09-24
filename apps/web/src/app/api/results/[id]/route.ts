/**
 * API route: retrieve batch results.
 *
 * GET /api/results/[id] — returns results of a completed batch job.
 */
import type { NextRequest } from "next/server";
import { configuredScorerUrl, serviceEndpoint } from "~/lib/scorer-endpoint";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id: jobId } = await params;
  const configuredUrl = configuredScorerUrl();
  if (!configuredUrl) {
    return Response.json(
      { error: "No research scoring service is configured" },
      { status: 503 },
    );
  }
  const resultsUrl = serviceEndpoint(configuredUrl, `/results/${jobId}`);

  try {
    const response = await fetch(resultsUrl);
    const data: unknown = await response.json();
    return Response.json(data, { status: response.status });
  } catch (error) {
    console.error("Batch results error:", error);
    return Response.json(
      { error: "Failed to get batch results" },
      { status: 500 },
    );
  }
}
