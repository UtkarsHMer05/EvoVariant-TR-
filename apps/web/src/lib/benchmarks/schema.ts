export const BENCHMARK_STATUSES = [
  "PASS",
  "COMPLETED_WITH_LIMITATIONS",
  "NOT_APPLICABLE",
  "DATA_BLOCKED",
  "COMPUTE_BLOCKED",
] as const;

export type BenchmarkStatus = (typeof BENCHMARK_STATUSES)[number];

export type BenchmarkEntry = {
  id: string;
  title: string;
  family: string;
  status: BenchmarkStatus;
  summary: string;
  question: string;
  population: string;
  n: number | null;
  metrics: string[];
  figures: string[];
  tables: string[];
  limitations: string[];
  code_links: string[];
  artifact_links: string[];
  provenance_links: string[];
  web_tab: string;
  new_inference: string;
};

export type BenchmarkFigure = {
  id: string;
  title: string;
  benchmark_id: string;
  population: string;
  n: number | null;
  caption: string;
  asset: string;
  source_data: string;
  provenance: string;
  sha256: Record<string, string>;
};

export type BenchmarkManifest = {
  schema_version: string;
  title: string;
  subtitle: string;
  status_vocabulary: BenchmarkStatus[];
  headline_cards: Array<{
    id: string;
    label: string;
    value: number | string | null;
    source: string;
  }>;
  what_we_contributed: Array<{
    benchmark_id: string;
    title: string;
    status: BenchmarkStatus;
    web_tab: string;
    evidence: string[];
  }>;
  tabs: Array<{ id: string; label: string; benchmark_ids: string[] }>;
  benchmarks: BenchmarkEntry[];
  figures: BenchmarkFigure[];
  data: Record<string, unknown>;
  fine_tuning: Record<string, unknown>;
  reproducibility: Record<string, unknown>;
  downloads: Array<{ label: string; path: string }>;
  limitations: string[];
};

export type JsonObject = Record<string, unknown>;

export function isJsonObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function asRecord(value: unknown): JsonObject {
  return isJsonObject(value) ? value : {};
}

export function asNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

export function asString(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}
