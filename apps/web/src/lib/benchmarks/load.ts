import {
  BENCHMARK_STATUSES,
  type BenchmarkManifest,
  isJsonObject,
} from "./schema";

function isStatus(value: unknown): boolean {
  return (
    typeof value === "string" &&
    BENCHMARK_STATUSES.includes(value as (typeof BENCHMARK_STATUSES)[number])
  );
}

export function validateBenchmarkManifest(
  value: unknown,
): asserts value is BenchmarkManifest {
  if (!isJsonObject(value))
    throw new Error("Benchmark manifest is not an object");
  if (typeof value.title !== "string" || typeof value.subtitle !== "string") {
    throw new Error("Benchmark manifest has no title or subtitle");
  }
  if (
    !Array.isArray(value.headline_cards) ||
    !Array.isArray(value.tabs) ||
    !Array.isArray(value.benchmarks)
  ) {
    throw new Error("Benchmark manifest is missing required collections");
  }
  if (
    !value.benchmarks.every(
      (entry) =>
        isJsonObject(entry) &&
        typeof entry.id === "string" &&
        isStatus(entry.status),
    )
  ) {
    throw new Error("Benchmark manifest contains an invalid benchmark entry");
  }
}

export async function loadBenchmarkManifest(
  signal?: AbortSignal,
): Promise<BenchmarkManifest> {
  const response = await fetch("/benchmarks/benchmark-manifest.json", {
    cache: "no-store",
    signal,
  });
  if (!response.ok)
    throw new Error(`Benchmark manifest request failed (${response.status})`);
  const value: unknown = await response.json();
  validateBenchmarkManifest(value);
  return value;
}
