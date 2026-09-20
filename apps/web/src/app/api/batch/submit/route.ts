/**
 * API route: batch variant submission.
 * 
 * POST /api/batch/submit — submits a batch of variants for scoring.
 */
import type { NextRequest } from "next/server";
import { env } from "~/env";

export async function POST(request: NextRequest) {
  try {
    const body: unknown = await request.json();
    const baseUrl = env.NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL;

    const response = await fetch(`${baseUrl}/batch/submit`, {
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
    return Response.json(
      { error: "Failed to submit batch" },
      { status: 500 },
    );
  }
}
