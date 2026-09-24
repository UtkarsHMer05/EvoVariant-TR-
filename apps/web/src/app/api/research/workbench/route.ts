import { createHash } from "node:crypto";
import { readFile, stat } from "node:fs/promises";
import path from "node:path";

export const dynamic = "force-dynamic";

type JsonObject = Record<string, unknown>;

const INVENTORY_PATH = "research/reports/phase17/FIGURE_INVENTORY.json";
const PHASE15_VALIDATION_PATH =
  "artifacts/phase15/phase15_parity_smoke_validation_20260922.json";

const AREA_FIGURES: Record<string, string[]> = {
  "temporal-vus": ["cohort_flow", "temporal_transition"],
  "model-benchmark": [
    "foundation_model_performance",
    "classifier_auroc_heatmap",
  ],
  representation: ["representation_layers", "raw_vs_representation"],
  "training-hpo": [
    "classifier_auroc_heatmap",
    "hpo_trial_history",
    "learning_curve_auroc",
  ],
  ensemble: ["diversity_matrix", "ensemble_comparison"],
  calibration: [
    "calibration_reliability",
    "calibration_metric_comparison",
    "risk_coverage_development",
  ],
  robustness: ["ablation_metric_delta", "context_length_metric"],
  "error-analysis": [
    "final_confusion_matrix",
    "final_error_chromosome",
    "final_gene_errors",
  ],
};

const AREA_NOTES: Record<string, string> = {
  "temporal-vus":
    "Hash-verified temporal cohort and transition evidence from the publication registry.",
  "model-benchmark":
    "Registered development benchmark evidence; final locked metrics remain stage-qualified.",
  representation:
    "Registered layer and raw-versus-representation evidence from the development boundary.",
  "training-hpo":
    "Registered validation-only model, HPO, and learning-curve artifacts.",
  "fine-tuning":
    "Phase 10 adaptation is explicitly deferred; no checkpoint or loss curve is presented.",
  ensemble: "Registered development diversity and ensemble comparisons.",
  calibration:
    "Registered development reliability, calibration, and risk-coverage artifacts.",
  robustness:
    "Registered ablation evidence; context-length is a documented conditional omission.",
  "error-analysis":
    "Registered final error and subgroup artifacts; no post-test tuning is performed.",
};

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

function numberText(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value)
    ? String(value)
    : "Unavailable";
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
      if (
        (
          await stat(
            path.join(
              /* turbopackIgnore: true */ candidate,
              "experiments",
              "registry",
              "runs",
            ),
          )
        ).isDirectory()
      ) {
        return candidate;
      }
    } catch {
      // Try the next known repository root.
    }
  }
  return null;
}

async function readJson(
  repoRoot: string,
  relativePath: string,
): Promise<JsonObject | null> {
  const target = path.resolve(repoRoot, relativePath);
  if (!target.startsWith(`${repoRoot}${path.sep}`)) return null;
  try {
    return asObject(
      JSON.parse(
        await readFile(/* turbopackIgnore: true */ target, "utf8"),
      ) as unknown,
    );
  } catch {
    return null;
  }
}

async function hashFile(
  repoRoot: string,
  relativePath: string,
): Promise<string | null> {
  const target = path.resolve(repoRoot, relativePath);
  if (!target.startsWith(`${repoRoot}${path.sep}`)) return null;
  try {
    return createHash("sha256")
      .update(await readFile(/* turbopackIgnore: true */ target))
      .digest("hex");
  } catch {
    return null;
  }
}

type FigureEvidence = {
  figure_id: string;
  title: string;
  status: string;
  evidence_stage: string;
  population: string;
  n: number | null;
  source_count: number;
  source_hash_prefixes: string[];
  source_hashes_verified: boolean;
};

async function figureEvidence(
  repoRoot: string,
  raw: unknown,
): Promise<FigureEvidence | null> {
  const figure = asObject(raw);
  if (!figure) return null;
  const sources = asArray(figure.source_artifacts);
  const sourceResults = await Promise.all(
    sources.map(async (source) => {
      const record = asObject(source);
      const sourcePath = asString(record?.path);
      const expected = asString(record?.sha256);
      const actual = sourcePath ? await hashFile(repoRoot, sourcePath) : null;
      return {
        expected,
        actual,
        prefix: expected ? expected.slice(0, 12) : null,
      };
    }),
  );
  return {
    figure_id: asString(figure.figure_id) ?? "unknown",
    title: asString(figure.title) ?? "Untitled registered figure",
    status: asString(figure.status) ?? "UNKNOWN",
    evidence_stage: asString(figure.evidence_stage) ?? "UNKNOWN",
    population: asString(figure.population) ?? "Unspecified population",
    n:
      typeof figure.n === "number" && Number.isFinite(figure.n)
        ? figure.n
        : null,
    source_count: sourceResults.length,
    source_hash_prefixes: sourceResults.flatMap((source) =>
      source.prefix ? [source.prefix] : [],
    ),
    source_hashes_verified: sourceResults.every(
      (source) => source.expected !== null && source.actual === source.expected,
    ),
  };
}

function areaStatus(
  figures: FigureEvidence[],
): "READY" | "PARTIAL" | "BLOCKED" {
  if (figures.length === 0) return "BLOCKED";
  if (
    figures.every(
      (figure) => figure.status === "READY" && figure.source_hashes_verified,
    )
  ) {
    return "PARTIAL";
  }
  return "BLOCKED";
}

function blockedAreas(): Record<
  string,
  {
    status: "BLOCKED";
    evidence_stage: string;
    note: string;
    figures: FigureEvidence[];
    summary: [];
  }
> {
  return Object.fromEntries(
    Object.keys(AREA_NOTES).map((area) => [
      area,
      {
        status: "BLOCKED" as const,
        evidence_stage: "UNAVAILABLE",
        note: AREA_NOTES[area] ?? "No registered evidence is available.",
        figures: [],
        summary: [],
      },
    ]),
  );
}

export async function GET() {
  const repoRoot = await findRepoRoot();
  if (!repoRoot) {
    return Response.json({
      status: "BLOCKED",
      manifest: null,
      areas: blockedAreas(),
      blockers: ["repository evidence root is unavailable"],
    });
  }

  const inventory = await readJson(repoRoot, INVENTORY_PATH);
  if (!inventory) {
    return Response.json({
      status: "BLOCKED",
      manifest: null,
      areas: blockedAreas(),
      blockers: ["hash-verified publication inventory is unavailable"],
    });
  }

  const rawFigures = asArray(inventory.figures);
  const indexedFigures = new Map<string, unknown>();
  for (const figure of rawFigures) {
    const figureObject = asObject(figure);
    const figureId = asString(figureObject?.figure_id);
    if (figureId) indexedFigures.set(figureId, figure);
  }

  const areas: Record<
    string,
    {
      status: "READY" | "PARTIAL" | "BLOCKED";
      evidence_stage: string;
      note: string;
      figures: FigureEvidence[];
      summary: Array<{ label: string; value: string }>;
    }
  > = {};
  for (const [area, figureIds] of Object.entries(AREA_FIGURES)) {
    const figures = (
      await Promise.all(
        figureIds.map((figureId) =>
          figureEvidence(repoRoot, indexedFigures.get(figureId)),
        ),
      )
    ).filter((figure): figure is FigureEvidence => figure !== null);
    areas[area] = {
      status: areaStatus(figures),
      evidence_stage: figures.some(
        (figure) => figure.evidence_stage === "FINAL",
      )
        ? "FINAL_AND_PRELIMINARY"
        : "PRELIMINARY",
      note: AREA_NOTES[area] ?? "No registered evidence is available.",
      figures,
      summary: [
        { label: "Registered figures", value: String(figures.length) },
        {
          label: "Verified source hashes",
          value: `${figures.filter((figure) => figure.source_hashes_verified).length}/${figures.length}`,
        },
      ],
    };
  }
  areas["fine-tuning"] = {
    status: "BLOCKED",
    evidence_stage: "DEFERRED",
    note: AREA_NOTES["fine-tuning"] ?? "Phase 10 adaptation is deferred.",
    figures: [],
    summary: [{ label: "Evidence", value: "Deferred by compute" }],
  };

  const phase15 = await readJson(repoRoot, PHASE15_VALIDATION_PATH);
  const phase15Checks = asObject(phase15?.checks);
  const phase15Passed =
    phase15?.status === "PASS_PHASE15_PARITY_AND_RESUME" &&
    phase15Checks !== null &&
    Object.values(phase15Checks).every((value) => value === true);
  const selection = asObject(phase15?.selection);
  areas.batch = {
    status: phase15Passed ? "PARTIAL" : "BLOCKED",
    evidence_stage: phase15Passed ? "DEVELOPMENT_SMOKE" : "UNAVAILABLE",
    note: phase15Passed
      ? "The authorized development-only parity smoke is complete; full-cohort batch execution remains separately gated."
      : "No hash-verified Phase 15 smoke artifact is available.",
    figures: [],
    summary: phase15Passed
      ? [
          { label: "Smoke status", value: "PASS" },
          {
            label: "Expected rows",
            value: numberText(selection?.expected_rows),
          },
          {
            label: "Verified cache rows",
            value: numberText(selection?.verified_cache_rows),
          },
          { label: "Remote rows", value: numberText(selection?.remote_rows) },
          { label: "Locked rows", value: "0" },
        ]
      : [],
  };

  return Response.json({
    status: "PARTIAL",
    manifest: {
      status: asString(inventory.status) ?? "UNKNOWN",
      figure_count: rawFigures.length,
      rendered_count: rawFigures.filter(
        (figure) => asString(asObject(figure)?.status) === "READY",
      ).length,
      sha256: await hashFile(repoRoot, INVENTORY_PATH),
    },
    areas,
    blockers: phase15Passed
      ? []
      : ["Phase 15 parity-smoke validation is unavailable or failed"],
  });
}
