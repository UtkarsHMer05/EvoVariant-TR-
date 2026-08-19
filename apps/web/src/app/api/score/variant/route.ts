/**
 * API route: proxy to Modal scoring endpoint.
 * 
 * POST /api/score/variant — scores a single variant via the deployed
 * evovariant-tr Modal service, transforming the response to match
 * the frontend's AnalysisResult interface.
 * 
 * Requires NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL to point at the
 * Modal web endpoint.
 */
import type { NextRequest } from "next/server";
import { env } from "~/env";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const baseUrl = env.NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL;

    const response = await fetch(baseUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return Response.json(
        { error: `Scoring failed: ${response.status} ${errorText}` },
        { status: response.status },
      );
    }

    const data = await response.json();

    const deltaScore = data.score_delta ?? 0;

    const transformed = {
      position: body.variant_position ?? 0,
      reference: body.reference ?? "",
      alternative: body.alternative ?? body.alternative?.toLowerCase() ?? "",
      delta_score: deltaScore,
      prediction: deltaScore < 0 ? "likely_pathogenic" : "likely_benign",
      classification_confidence: Math.min(1.0, Math.abs(deltaScore) / 0.01),
    };

    return Response.json(transformed, { status: 200 });
  } catch (error) {
    console.error("Scoring error:", error);
    return Response.json(
      { error: "Failed to score variant" },
      { status: 500 },
    );
  }
}
