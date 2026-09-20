/**
 * API route: retrieve batch results.
 * 
 * GET /api/results/[id] — returns results of a completed batch job.
 */
import type { NextRequest } from "next/server";
import { env } from "~/env";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id: jobId } = await params;
  const baseUrl = env.NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL;

  try {
    const response = await fetch(`${baseUrl}/results/${jobId}`);
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
