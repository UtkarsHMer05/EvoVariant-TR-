import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";

export const dynamic = "force-dynamic";

const TERMINAL_STATUSES = new Set(["COMPLETED", "FAILED", "ABORTED"]);
const SCIENTIFIC_STAGES = new Set(["PRELIMINARY", "FINAL"]);

type RegistryRecord = {
  run_id: unknown;
  title: unknown;
  status: unknown;
  evidence_stage: unknown;
  experiment_family?: unknown;
  model_name?: unknown;
  created_at?: unknown;
  completed_at?: unknown;
  output_paths?: unknown;
};

type RegistryRunSummary = {
  run_id: string;
  title: string;
  status: string;
  evidence_stage: string;
  experiment_family: string;
  model_name: string | null;
  created_at: string | null;
  completed_at: string | null;
  artifact_count: number;
};

function asRequiredString(value: unknown, field: string, source: string): string {
  if (typeof value !== "string" || !value.trim()) {
    throw new Error(`${source}: ${field} must be a non-empty string`);
  }
  return value;
}

function asOptionalString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function parseRunRecord(raw: unknown, source: string): RegistryRunSummary {
  if (typeof raw !== "object" || raw === null || Array.isArray(raw)) {
    throw new Error(`${source}: record must be an object`);
  }

  const record = raw as RegistryRecord;
  const status = asRequiredString(record.status, "status", source);
  if (!TERMINAL_STATUSES.has(status) && !["REGISTERED", "RUNNING"].includes(status)) {
    throw new Error(`${source}: unsupported status ${status}`);
  }

  const outputPaths = record.output_paths;
  if (outputPaths !== undefined && !Array.isArray(outputPaths)) {
    throw new Error(`${source}: output_paths must be an array when present`);
  }

  return {
    run_id: asRequiredString(record.run_id, "run_id", source),
    title: asRequiredString(record.title, "title", source),
    status,
    evidence_stage: asRequiredString(record.evidence_stage, "evidence_stage", source),
    experiment_family:
      asOptionalString(record.experiment_family) ?? "UNSPECIFIED",
    model_name: asOptionalString(record.model_name),
    created_at: asOptionalString(record.created_at),
    completed_at: asOptionalString(record.completed_at),
    artifact_count: outputPaths?.length ?? 0,
  };
}

async function findRunsDirectory(): Promise<string | null> {
  const configuredRoot = process.env.EVOVARIANT_REPO_ROOT;
  const candidates = [
    configuredRoot,
    path.resolve(process.cwd(), "../.."),
    process.cwd(),
  ].filter((candidate): candidate is string => Boolean(candidate));

  for (const candidate of [...new Set(candidates)]) {
    const runsDirectory = path.join(candidate, "experiments", "registry", "runs");
    try {
      if ((await stat(runsDirectory)).isDirectory()) return runsDirectory;
    } catch {
      // Try the next known repository-root candidate.
    }
  }
  return null;
}

export async function GET() {
  try {
    const runsDirectory = await findRunsDirectory();
    if (!runsDirectory) {
      return Response.json({
        status: "BLOCKED",
        registered_run_count: 0,
        completed_scientific_run_count: 0,
        artifact_count: 0,
        blockers: ["registry run directory is unavailable"],
        runs: [],
      });
    }

    const filenames = (await readdir(runsDirectory))
      .filter((filename) => /^run_[^/]+\.json$/.test(filename))
      .sort()
      .reverse();
    const runs: RegistryRunSummary[] = [];

    for (const filename of filenames) {
      const source = path.join(runsDirectory, filename);
      const raw = JSON.parse(await readFile(source, "utf8")) as unknown;
      runs.push(parseRunRecord(raw, filename));
    }

    const completedScientificRunCount = runs.filter(
      (run) =>
        run.status === "COMPLETED" &&
        SCIENTIFIC_STAGES.has(run.evidence_stage),
    ).length;
    const artifactCount = runs.reduce((total, run) => total + run.artifact_count, 0);
    const ready = completedScientificRunCount > 0;

    return Response.json({
      status: ready ? "READY" : "BLOCKED",
      registered_run_count: runs.length,
      completed_scientific_run_count: completedScientificRunCount,
      artifact_count: artifactCount,
      blockers: ready
        ? []
        : ["no completed scientific run records are registered"],
      runs,
    });
  } catch (error) {
    const detail = error instanceof Error ? error.message : "unknown registry error";
    return Response.json(
      { error: "Registry metadata unavailable", detail },
      { status: 500 },
    );
  }
}
