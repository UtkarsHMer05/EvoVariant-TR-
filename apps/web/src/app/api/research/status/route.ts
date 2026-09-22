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

const FINAL_LOCKED_ARTIFACT = "artifacts/phase14/phase14_locked_evo2_20260922.json";

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

function asNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

async function readVerifiedFinalEvaluation(
  repoRoot: string,
): Promise<{ runId: string; artifact: JsonObject; artifactSha256: string } | null> {
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
      record?.status !== "COMPLETED" ||
      record?.evidence_stage !== "FINAL" ||
      record?.experiment_family !== "PHASE14_LOCKED_EVALUATION"
    ) {
      continue;
    }
    const outputHashes = asObject(record.output_hashes);
    const expectedArtifactSha256 = asString(outputHashes?.[FINAL_LOCKED_ARTIFACT]);
    const actualArtifactSha256 = await sha256(repoRoot, FINAL_LOCKED_ARTIFACT);
    if (!expectedArtifactSha256 || expectedArtifactSha256 !== actualArtifactSha256) continue;
    const artifact = await readJson(repoRoot, FINAL_LOCKED_ARTIFACT);
    const gates = asObject(artifact?.integrity_gates);
    if (
      artifact?.status !== "PASS_PHASE14_LOCKED_EVALUATION" ||
      !gates ||
      !Object.values(gates).every((value) => value === true)
    ) {
      continue;
    }
    return {
      runId: asString(record.run_id) ?? filename.replace(/\.json$/, ""),
      artifact,
      artifactSha256: actualArtifactSha256,
    };
  }
  return null;
}

function phaseStatus(output: JsonObject | null): string {
  return asString(output?.status) ?? "UNAVAILABLE";
}

function blockedEvidence(blockers: string[]) {
  return {
    status: "BLOCKED",
    evidence_stage: "UNAVAILABLE",
    locked_test_evaluated: false,
    selection_closed: false,
    ui: { status: "BLOCKED", registered_run_count: null },
    development: {
      classifier_combinations: 0,
      hpo_studies: 0,
      phases: [8, 9, 11, 12, 13].map((phase) => ({
        phase,
        status: "UNAVAILABLE",
      })),
    },
    figures: {
      status: "BLOCKED",
      available_figures: 0,
      required_figures: 19,
      available_tables: 0,
      required_tables: 11,
      blockers,
    },
  } as const;
}

export async function GET() {
  const repoRoot = await findRepoRoot();
  if (!repoRoot) {
    return Response.json(blockedEvidence(["repository evidence root is unavailable"]));
  }

  const verified = await readVerifiedFormalOutputs(repoRoot);
  const finalEvaluation = await readVerifiedFinalEvaluation(repoRoot);
  const figureStatus = await readJson(repoRoot, "research/runs/phase17_fig_status.json");
  const uiStatus = await readJson(repoRoot, "research/runs/phase16_ui_status.json");
  if (!verified || !figureStatus) {
    return Response.json(
      blockedEvidence([
        ...(!verified ? ["hash-verified formal development outputs are unavailable"] : []),
        ...(!figureStatus ? ["registry-driven figure status is unavailable"] : []),
      ]),
    );
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
  const finalArtifact = finalEvaluation?.artifact;
  const finalMetrics = asObject(finalArtifact?.metrics);
  const finalProbabilityMetrics = asObject(finalMetrics?.probability_metrics);
  const finalCohort = asObject(finalArtifact?.locked_cohort);
  const finalSubmission = asObject(finalArtifact?.submission);
  const finalOutputs = asObject(finalArtifact?.outputs);
  const finalCiValues = Array.isArray(finalMetrics?.bootstrap_auc_ci95)
    ? finalMetrics.bootstrap_auc_ci95.map(asNumber)
    : [];
  const finalCi = finalCiValues.length === 2
    && finalCiValues[0] !== null
    && finalCiValues[1] !== null
    ? [finalCiValues[0], finalCiValues[1]]
    : null;

  return Response.json({
    status: "PARTIAL",
    evidence_stage: finalEvaluation ? "FINAL" : "PRELIMINARY",
    locked_test_evaluated: finalEvaluation !== null,
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
    final_evaluation: finalEvaluation
      ? {
          run_id: finalEvaluation.runId,
          status: finalArtifact?.status,
          completed_rows: asNumber(finalCohort?.completed_rows),
          expected_rows: asNumber(finalCohort?.expected_rows),
          submitted_rows: asNumber(finalSubmission?.submitted_rows),
          model_contract: finalArtifact?.model_contract ?? null,
          auroc: asNumber(finalMetrics?.auroc),
          auprc: asNumber(finalMetrics?.auprc),
          bootstrap_auc_ci95: finalCi,
          accuracy: asNumber(finalProbabilityMetrics?.accuracy),
          brier: asNumber(finalProbabilityMetrics?.brier),
          nll: asNumber(finalProbabilityMetrics?.nll),
          ece: asNumber(finalProbabilityMetrics?.ece),
          coverage: asNumber(asObject(finalMetrics?.abstention)?.actual_coverage),
          abstention_risk: asNumber(asObject(finalMetrics?.abstention)?.risk),
          artifact_sha256: finalEvaluation.artifactSha256,
          raw_predictions_sha256: asString(finalOutputs?.raw_predictions_sha256),
          joined_predictions_sha256: asString(finalOutputs?.local_label_join_sha256),
          integrity_gates_passed: true,
        }
      : null,
  });
}
