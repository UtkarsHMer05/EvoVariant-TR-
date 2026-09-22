import { createHash } from "node:crypto";
import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";

export const dynamic = "force-dynamic";

type JsonObject = Record<string, unknown>;
type FormalOutputs = [
  JsonObject,
  JsonObject,
  JsonObject,
  JsonObject,
  JsonObject,
];

const FORMAL_OUTPUTS = [
  "research/runs/formal_cpu_20260922/phase8/summary.json",
  "research/runs/formal_cpu_20260922/phase9/summary.json",
  "research/runs/formal_cpu_20260922/phase11/ensemble_analysis.json",
  "research/runs/formal_cpu_20260922/phase12/calibration_abstention.json",
  "research/runs/formal_cpu_20260922/phase13/ablations_learning_curves_robustness.json",
  "research/runs/formal_cpu_20260922/phase13/pre_phase14_freeze.json",
] as const;

const PARSED_FORMAL_OUTPUTS = [
  "research/runs/formal_cpu_20260922/phase8/summary.json",
  "research/runs/formal_cpu_20260922/phase9/summary.json",
  "research/runs/formal_cpu_20260922/phase11/ensemble_analysis.json",
  "research/runs/formal_cpu_20260922/phase13/ablations_learning_curves_robustness.json",
  "research/runs/formal_cpu_20260922/phase13/pre_phase14_freeze.json",
] as const;

function asObject(value: unknown): JsonObject | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as JsonObject)
    : null;
}

function asString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

async function findRepoRoot(): Promise<string | null> {
  const configuredRoot = process.env.EVOVARIANT_REPO_ROOT;
  const candidates = [
    configuredRoot,
    path.resolve(process.cwd(), "../.."),
    process.cwd(),
  ].filter((candidate): candidate is string => Boolean(candidate));

  for (const candidate of [...new Set(candidates)]) {
    try {
      if ((await stat(path.join(candidate, "experiments", "registry", "runs"))).isDirectory()) {
        return candidate;
      }
    } catch {
      // Try the next known repository-root candidate.
    }
  }
  return null;
}

async function readJson(repoRoot: string, relativePath: string): Promise<JsonObject | null> {
  const target = path.resolve(repoRoot, relativePath);
  if (!target.startsWith(`${repoRoot}${path.sep}`)) return null;
  try {
    return asObject(JSON.parse(await readFile(target, "utf8")) as unknown);
  } catch {
    return null;
  }
}

async function sha256(repoRoot: string, relativePath: string): Promise<string | null> {
  const target = path.resolve(repoRoot, relativePath);
  if (!target.startsWith(`${repoRoot}${path.sep}`)) return null;
  try {
    return createHash("sha256").update(await readFile(target)).digest("hex");
  } catch {
    return null;
  }
}

async function readVerifiedFormalOutputs(
  repoRoot: string,
): Promise<{ record: JsonObject; outputs: FormalOutputs } | null> {
  const recordsDirectory = path.join(repoRoot, "experiments", "registry", "runs");
  let filenames: string[];
  try {
    filenames = (await readdir(recordsDirectory)).filter((filename) =>
      /^run_[^/]+\.json$/.test(filename),
    );
  } catch {
    return null;
  }

  for (const filename of filenames) {
    const record = await readJson(repoRoot, path.join("experiments/registry/runs", filename));
    if (
      record?.experiment_family !== "FORMAL_CPU" ||
      record?.status !== "COMPLETED" ||
      record?.evidence_stage !== "PRELIMINARY"
    ) {
      continue;
    }
    const outputHashes = asObject(record.output_hashes);
    const outputPaths = asArray(record.output_paths).filter(
      (value): value is string => typeof value === "string",
    );
    if (!outputHashes || !FORMAL_OUTPUTS.every((output) => outputPaths.includes(output))) {
      continue;
    }
    const verified = await Promise.all(
      FORMAL_OUTPUTS.map(async (output) => {
        const expected = asString(outputHashes[output]);
        const actual = await sha256(repoRoot, output);
        return expected !== null && actual !== null && expected === actual;
      }),
    );
    if (!verified.every(Boolean)) continue;
    const outputs = await Promise.all(
      PARSED_FORMAL_OUTPUTS.map((output) => readJson(repoRoot, output)),
    );
    if (outputs.every((output): output is JsonObject => output !== null)) {
      return { record, outputs: outputs as FormalOutputs };
    }
  }
  return null;
}

function phaseStatus(output: JsonObject | null): string {
  return asString(output?.status) ?? "UNAVAILABLE";
}

export async function GET() {
  const repoRoot = await findRepoRoot();
  if (!repoRoot) {
    return Response.json({
      status: "BLOCKED",
      blockers: ["repository evidence root is unavailable"],
    });
  }

  const verified = await readVerifiedFormalOutputs(repoRoot);
  const figureStatus = await readJson(repoRoot, "research/runs/phase17_fig_status.json");
  const uiStatus = await readJson(repoRoot, "research/runs/phase16_ui_status.json");
  if (!verified || !figureStatus) {
    return Response.json({
      status: "BLOCKED",
      blockers: ["hash-verified formal development outputs are unavailable"],
      locked_test_evaluated: false,
    });
  }

  const { record, outputs } = verified;
  const [phase8, phase9, phase11, phase13, freeze] = outputs;
  const runMetrics = asObject(record.metrics);
  const requiredFigures = asArray(figureStatus.required_figures);
  const availableFigures = asArray(figureStatus.available_figures);
  const requiredTables = asArray(figureStatus.required_tables);
  const availableTables = asArray(figureStatus.available_tables);
  const blockers = asArray(figureStatus.blockers).filter(
    (value): value is string => typeof value === "string",
  );
  const selectionClosed = freeze.selection_closed === true;

  return Response.json({
    status: "PARTIAL",
    evidence_stage: "PRELIMINARY",
    locked_test_evaluated: false,
    selection_closed: selectionClosed,
    ui: {
      status: asString(uiStatus?.status) ?? "PARTIAL",
      registered_run_count: uiStatus?.registered_run_count ?? null,
    },
    development: {
      classifier_combinations: asArray(phase8.models).length,
      hpo_studies: Object.keys(asObject(phase9.studies) ?? {}).length,
      phases: [
        { phase: 8, status: phaseStatus(phase8) },
        { phase: 9, status: phaseStatus(phase9) },
        { phase: 11, status: phaseStatus(phase11) },
        { phase: 12, status: asString(runMetrics?.phase12_status) ?? "UNAVAILABLE" },
        { phase: 13, status: phaseStatus(phase13) },
      ],
    },
    figures: {
      status: asString(figureStatus.status) ?? "BLOCKED",
      available_figures: availableFigures.length,
      required_figures: requiredFigures.length,
      available_tables: availableTables.length,
      required_tables: figureStatus.applicable_required_table_count ?? requiredTables.length,
      blockers,
    },
  });
}
