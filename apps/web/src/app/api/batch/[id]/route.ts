/**
 * API route: batch job status.
 *
 * GET /api/batch/[id] — returns status of a batch job.
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
  const statusUrl = serviceEndpoint(configuredUrl, `/batch/${jobId}`);

  try {
    const response = await fetch(statusUrl);
    const data: unknown = await response.json();
    return Response.json(data, { status: response.status });
  } catch (error) {
    console.error("Batch status error:", error);
    return Response.json(
      { error: "Failed to get batch status" },
      { status: 500 },
    );
  }
}
