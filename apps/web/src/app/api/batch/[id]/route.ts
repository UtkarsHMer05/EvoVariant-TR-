/**
 * API route: batch job status.
 * 
 * GET /api/batch/[id] — returns status of a batch job.
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
    const response = await fetch(`${baseUrl}/batch/${jobId}`);
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
