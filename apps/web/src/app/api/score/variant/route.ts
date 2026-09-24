/**
 * Research scoring transport route.
 *
 * This route validates and normalizes transport fields, then forwards raw
 * scorer output. It deliberately contains no threshold, confidence, or
 * pathogenic/benign classification logic.
 */
import type { NextRequest } from "next/server";
import { configuredScorerUrl, scoreEndpoint } from "~/lib/scorer-endpoint";

type JsonObject = Record<string, unknown>;

function isJsonObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requiredString(body: JsonObject, ...keys: string[]): string | null {
  for (const key of keys) {
    const value = body[key];
    if (typeof value === "string" && value.trim().length > 0) return value;
  }
  return null;
}

function requiredPosition(body: JsonObject): number | null {
  const raw = body.position_1based ?? body.variant_position ?? body.start;
  const position = typeof raw === "number" ? raw : Number(raw);
  return Number.isInteger(position) && position > 0 ? position : null;
}

export async function POST(request: NextRequest) {
  try {
    const rawBody: unknown = await request.json();
    if (!isJsonObject(rawBody)) {
      return Response.json(
        { error: "Request body must be a JSON object" },
        { status: 400 },
      );
    }

    const chromosome = requiredString(rawBody, "chromosome", "chrom");
    const reference = requiredString(rawBody, "reference", "ref");
    const alternate = requiredString(
      rawBody,
      "alternate",
      "alternative",
      "alt",
    );
    const position = requiredPosition(rawBody);
    if (!chromosome || !reference || !alternate || position === null) {
      return Response.json(
        {
          error:
            "Canonical scoring requires chromosome, position_1based, reference, and alternate",
        },
        { status: 422 },
      );
    }

    const configuredUrl = configuredScorerUrl();
    if (!configuredUrl) {
      return Response.json(
        { error: "No research scoring service is configured" },
        { status: 503 },
      );
    }
    const baseUrl = scoreEndpoint(configuredUrl);

    const orientation = rawBody.orientation ?? rawBody.strand ?? "both";
    const payload = {
      assembly: "GRCh38",
      chromosome,
      position_1based: position,
      reference: reference.toUpperCase(),
      alternate: alternate.toUpperCase(),
      orientation,
    };

    const response = await fetch(baseUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const responseText = await response.text();
    let data: unknown = null;
    try {
      data = responseText ? (JSON.parse(responseText) as unknown) : null;
    } catch {
      data = { error: responseText || `Scoring failed: ${response.status}` };
    }

    if (!response.ok) {
      return Response.json(
        isJsonObject(data)
          ? data
          : { error: `Scoring failed: ${response.status}` },
        { status: response.status },
      );
    }

    if (!isJsonObject(data)) {
      return Response.json(
        { error: "Scoring service returned an invalid response" },
        { status: 502 },
      );
    }

    // Forward raw/provenance fields without deriving a scientific label.
    return Response.json(data, { status: 200 });
  } catch (error) {
    console.error("Research scoring transport error:", error);
    return Response.json(
      { error: "Failed to reach the configured research scoring service" },
      { status: 502 },
    );
  }
}
