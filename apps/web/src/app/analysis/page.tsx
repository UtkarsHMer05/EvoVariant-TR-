"use client";

import { useState } from "react";
import { AlertCircle, Shield } from "lucide-react";
import { Alert, AlertDescription } from "~/components/ui/alert";
import { Button } from "~/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "~/components/ui/card";
import { Input } from "~/components/ui/input";
import { Label } from "~/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "~/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "~/components/ui/tabs";

type ScoreResponse = {
  variant: string;
  normalized_variant_id: string;
  assembly: string;
  chromosome: string;
  position_1based: number;
  reference: string;
  alternate: string;
  reference_score: number;
  alternate_score: number;
  score_delta: number;
  delta_forward: number | null;
  delta_reverse: number | null;
  delta_primary: number;
  orientation_disagreement: number | null;
  status: string;
  provenance: {
    scorer: string;
    scorer_version: string;
    orientation_requested: string;
    context_length_bp: number;
    research_only: boolean;
  };
};

type ProtocolInfo = {
  protocol_version: string;
  ml_extension_protocol_version: string;
  frozen_at: string;
  identity: string;
  context_length_bp: number;
  research_only: boolean;
  classification_logic: string;
};

type WorkbenchStatus = "READY" | "BLOCKED" | "PENDING";

type ResearchArea = {
  id: string;
  label: string;
  phase: string;
  status: WorkbenchStatus;
  description: string;
  artifact: string;
};

const CHROMOSOMES = [
  "chr1", "chr2", "chr3", "chr4", "chr5", "chr6", "chr7", "chr8",
  "chr9", "chr10", "chr11", "chr12", "chr13", "chr14", "chr15",
  "chr16", "chr17", "chr18", "chr19", "chr20", "chr21", "chr22",
  "chrX", "chrY", "chrM",
];

const RESEARCH_AREAS: ResearchArea[] = [
  {
    id: "overview",
    label: "Overview",
    phase: "Control plane",
    status: "READY",
    description: "Evidence, dependencies, and registered outputs at a glance.",
    artifact: "Project-control files and phase ledger",
  },
  {
    id: "single-variant",
    label: "Single Variant Research Analysis",
    phase: "Phase 2",
    status: "READY",
    description: "Canonical GRCh38 input with raw forward and reverse-complement signals.",
    artifact: "Research scoring API response",
  },
  {
    id: "temporal-vus",
    label: "Temporal VUS Explorer",
    phase: "Phase 3 / 6",
    status: "BLOCKED",
    description: "t0-to-t1 cohort flow, model signals, disagreement, and review status.",
    artifact: "Registered temporal benchmark rows",
  },
  {
    id: "model-benchmark",
    label: "Model Benchmark",
    phase: "Phase 6",
    status: "BLOCKED",
    description: "Comparable zero-shot outputs, score direction, coverage, and runtime.",
    artifact: "Zero-shot result registry entries",
  },
  {
    id: "representation",
    label: "Representation / Layer Analysis",
    phase: "Phase 7",
    status: "BLOCKED",
    description: "Frozen ref/alt representations, layer selection, and storage evidence.",
    artifact: "Verified feature-cache manifest",
  },
  {
    id: "training-hpo",
    label: "Training & Hyperparameter Experiments",
    phase: "Phases 8–9",
    status: "BLOCKED",
    description: "Validation-only trials, curves, seeds, and frozen development configs.",
    artifact: "Training and HPO run manifests",
  },
  {
    id: "fine-tuning",
    label: "Fine-Tuning Experiments",
    phase: "Phase 10",
    status: "BLOCKED",
    description: "PEFT or full adaptation smoke evidence, checkpoints, and recovery notes.",
    artifact: "Adaptation checkpoint manifest",
  },
  {
    id: "ensemble",
    label: "Ensemble Analysis",
    phase: "Phase 11",
    status: "BLOCKED",
    description: "Diversity, error overlap, out-of-fold stacking, and validation selection.",
    artifact: "OOF and ensemble comparison artifacts",
  },
  {
    id: "calibration",
    label: "Calibration & Abstention",
    phase: "Phase 12",
    status: "BLOCKED",
    description: "Reliability, uncertainty, risk coverage, and validation-frozen thresholds.",
    artifact: "Calibration and abstention manifest",
  },
  {
    id: "robustness",
    label: "Robustness & Ablation",
    phase: "Phase 13",
    status: "BLOCKED",
    description: "Predeclared context, orientation, feature, subgroup, and seed comparisons.",
    artifact: "Ablation matrix and robustness results",
  },
  {
    id: "error-analysis",
    label: "Error Analysis",
    phase: "Phase 13 / 14",
    status: "BLOCKED",
    description: "Failure cases and subgroup diagnostics from registered predictions.",
    artifact: "Error-analysis report artifact",
  },
  {
    id: "batch",
    label: "Batch VCF/CSV",
    phase: "Phase 15",
    status: "BLOCKED",
    description: "Validated ingest, resumable execution, progress, partial failure, and export.",
    artifact: "Batch manifest and result export",
  },
  {
    id: "methods-provenance",
    label: "Methods & Provenance",
    phase: "Control plane",
    status: "READY",
    description: "Frozen protocol identity, limitations, and research-only boundaries.",
    artifact: "Protocol and provenance metadata",
  },
  {
    id: "registry",
    label: "Experiment Registry",
    phase: "All phases",
    status: "BLOCKED",
    description: "Immutable run metadata, artifact hashes, cost, and failure reasons.",
    artifact: "Registered experiment manifests",
  },
];

function statusClasses(status: WorkbenchStatus): string {
  if (status === "READY") return "bg-[#e8f2e8] text-[#3c4f3d]";
  if (status === "BLOCKED") return "bg-[#fff0e7] text-[#a55424]";
  return "bg-[#eef0ef] text-[#536054]";
}

function StatusPill({ status }: { status: WorkbenchStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-1 text-[10px] font-medium tracking-[0.12em] ${statusClasses(status)}`}
    >
      {status}
    </span>
  );
}

function readErrorDetail(value: unknown): string | null {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return null;
  }
  const payload = value as Record<string, unknown>;
  for (const key of ["detail", "error"]) {
    if (typeof payload[key] === "string" && payload[key].trim()) {
      return payload[key];
    }
  }
  return null;
}

function EmptyAreaPanel({ area }: { area: ResearchArea }) {
  return (
    <Card className="gap-0 border-none bg-white py-0 shadow-sm">
      <CardHeader className="border-b border-[#3c4f3d]/10 py-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="text-base font-normal text-[#3c4f3d]">
              {area.label}
            </CardTitle>
            <CardDescription className="mt-2 max-w-2xl text-sm text-[#3c4f3d]/65">
              {area.description}
            </CardDescription>
          </div>
          <StatusPill status={area.status} />
        </div>
      </CardHeader>
      <CardContent className="space-y-4 py-5">
        <div className="rounded-md border border-dashed border-[#3c4f3d]/20 bg-[#f7f9f7] p-4">
          <p className="text-sm font-medium text-[#3c4f3d]">
            No registered scientific output is available for this area.
          </p>
          <p className="mt-1 text-sm leading-6 text-[#3c4f3d]/65">
            This is an intentional evidence-gated empty state. The workbench does not
            invent metrics, curves, model scores, or classifications while its required
            upstream artifact is missing.
          </p>
        </div>
        <dl className="grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-xs uppercase tracking-[0.12em] text-[#3c4f3d]/50">Phase</dt>
            <dd className="mt-1 text-[#3c4f3d]">{area.phase}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-[0.12em] text-[#3c4f3d]/50">
              Expected artifact
            </dt>
            <dd className="mt-1 text-[#3c4f3d]">{area.artifact}</dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}

export default function VariantAnalysisPage() {
  const [chrom, setChrom] = useState("chr17");
  const [position, setPosition] = useState("43044295");
  const [ref, setRef] = useState("C");
  const [alt, setAlt] = useState("T");
  const [orientation, setOrientation] = useState("both");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ScoreResponse | null>(null);
  const [protocol, setProtocol] = useState<ProtocolInfo | null>(null);

  const handleSubmit = async () => {
    const numericPosition = Number(position);
    if (!Number.isInteger(numericPosition) || numericPosition < 1 || !ref || !alt) {
      setError("A positive integer position, ref, and alt are required.");
      return;
    }
    if (ref.toUpperCase() === alt.toUpperCase()) {
      setError("Reference and alternate alleles must differ.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/score/variant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          assembly: "GRCh38",
          chromosome: chrom,
          position_1based: numericPosition,
          reference: ref,
          alternate: alt,
          orientation,
        }),
      });

      if (!response.ok) {
        const payload: unknown = await response.json();
        throw new Error(readErrorDetail(payload) ?? "Scoring failed");
      }

      const data = (await response.json()) as ScoreResponse;
      setResult(data);
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : "An error occurred",
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadProtocol = async () => {
    try {
      const response = await fetch("/api/protocol");
      if (!response.ok) throw new Error("Protocol metadata is unavailable");
      const data = (await response.json()) as ProtocolInfo;
      setProtocol(data);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Protocol metadata is unavailable",
      );
    }
  };

  const loadExample = () => {
    setChrom("chr17");
    setPosition("43044295");
    setRef("C");
    setAlt("T");
    setError(null);
  };

  const nonInteractiveAreas = RESEARCH_AREAS.filter(
    (area) => !["overview", "single-variant", "methods-provenance"].includes(area.id),
  );

  return (
    <div className="min-h-screen bg-[#e9eeea]">
      <header className="border-b border-[#3c4f3d]/10 bg-white">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <Shield className="h-6 w-6 text-[#de8246]" aria-hidden="true" />
            <div>
              <h1 className="text-xl font-light tracking-wide text-[#3c4f3d]">
                EvoVariant-TR Research Workbench
              </h1>
              <p className="mt-1 text-xs text-[#3c4f3d]/60">
                Evidence-gated temporal variant research · no clinical classification
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        <Tabs defaultValue="overview" className="space-y-6">
          <div className="w-full overflow-x-auto pb-1" aria-label="Research workbench areas">
            <TabsList className="min-w-max bg-[#e9eeea]">
              {RESEARCH_AREAS.map((area) => (
                <TabsTrigger
                  key={area.id}
                  value={area.id}
                  className="data-[state=active]:bg-white data-[state=active]:text-[#3c4f3d]"
                >
                  {area.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </div>

          <TabsContent value="overview" className="space-y-6">
            <section aria-labelledby="overview-heading">
              <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.16em] text-[#de8246]">Overview</p>
                  <h2 id="overview-heading" className="mt-1 text-2xl font-light text-[#3c4f3d]">
                    Research status, not a toy classifier
                  </h2>
                </div>
                <p className="max-w-lg text-right text-sm leading-6 text-[#3c4f3d]/65">
                  Every result panel is backed by a registered artifact. Missing evidence is
                  shown as blocked or pending and never replaced with placeholder metrics.
                </p>
              </div>

              <Alert className="border-[#de8246]/30 bg-[#fff8f2] text-[#3c4f3d]">
                <AlertCircle className="h-4 w-4 text-[#de8246]" aria-hidden="true" />
                <AlertDescription>
                  Research-only surface. The current registry has no included model outputs;
                  remote compute and downstream scientific selection remain gated by the
                  project-control files.
                </AlertDescription>
              </Alert>
            </section>

            <div className="grid gap-4 md:grid-cols-4">
              {[
                ["Protocol", "READY", "Frozen control plane"],
                ["Model registry", "BLOCKED", "No included model"],
                ["Compute pilot", "BLOCKED", "No remote invocation"],
                ["Result registry", "BLOCKED", "No promoted outputs"],
              ].map(([label, status, detail]) => (
                <div key={label} className="border-l-2 border-[#3c4f3d]/15 bg-white px-4 py-4 shadow-sm">
                  <p className="text-xs uppercase tracking-[0.12em] text-[#3c4f3d]/50">{label}</p>
                  <div className="mt-3 flex items-center justify-between gap-2">
                    <span className="text-sm font-medium text-[#3c4f3d]">{detail}</span>
                    <StatusPill status={status as WorkbenchStatus} />
                  </div>
                </div>
              ))}
            </div>

            <Card className="gap-0 border-none bg-white py-0 shadow-sm">
              <CardHeader className="border-b border-[#3c4f3d]/10 py-5">
                <CardTitle className="text-base font-normal text-[#3c4f3d]">
                  Workbench map
                </CardTitle>
                <CardDescription className="text-sm text-[#3c4f3d]/65">
                  Open any area from the navigation above to inspect its artifact contract or
                  evidence-gated empty state.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-x-8 gap-y-1 py-3 md:grid-cols-2">
                {RESEARCH_AREAS.map((area) => (
                  <div
                    key={area.id}
                    className="flex items-center justify-between gap-4 border-b border-[#3c4f3d]/8 py-3"
                  >
                    <div>
                      <p className="text-sm text-[#3c4f3d]">{area.label}</p>
                      <p className="mt-1 text-xs text-[#3c4f3d]/55">
                        {area.phase} · {area.artifact}
                      </p>
                    </div>
                    <StatusPill status={area.status} />
                  </div>
                ))}
              </CardContent>
            </Card>

            <div className="grid gap-4 md:grid-cols-3">
              {["Trials and learning curves", "Model differences and errors", "Cost and reproducibility"].map(
                (label) => (
                  <div key={label} className="rounded-lg border border-dashed border-[#3c4f3d]/20 bg-white/60 p-4">
                    <p className="text-sm font-medium text-[#3c4f3d]">{label}</p>
                    <p className="mt-2 text-sm leading-6 text-[#3c4f3d]/60">
                      Awaiting a registered artifact. The dashboard will populate this view
                      from the experiment registry when its dependency passes.
                    </p>
                  </div>
                ),
              )}
            </div>
          </TabsContent>

          <TabsContent value="single-variant" className="space-y-6">
            <Card className="gap-0 border-none bg-white py-0 shadow-sm">
              <CardHeader className="pt-5 pb-3">
                <CardTitle className="text-base font-normal text-[#3c4f3d]">
                  Single Variant Research Analysis
                </CardTitle>
                <CardDescription className="text-sm text-[#3c4f3d]/65">
                  Canonical GRCh38 input. The endpoint returns raw research signals only.
                </CardDescription>
              </CardHeader>
              <CardContent className="pb-6">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
                  <div>
                    <Label className="text-xs font-normal text-[#3c4f3d]/70">Chromosome</Label>
                    <Select value={chrom} onValueChange={setChrom}>
                      <SelectTrigger className="h-9 border-[#3c4f3d]/10">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {CHROMOSOMES.map((chromosome) => (
                          <SelectItem key={chromosome} value={chromosome}>
                            {chromosome}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-xs font-normal text-[#3c4f3d]/70">Position (1-based)</Label>
                    <Input
                      type="number"
                      min="1"
                      value={position}
                      onChange={(event) => setPosition(event.target.value)}
                      className="h-9 border-[#3c4f3d]/10"
                    />
                  </div>
                  <div>
                    <Label className="text-xs font-normal text-[#3c4f3d]/70">Reference Allele</Label>
                    <Input
                      type="text"
                      maxLength={1}
                      value={ref}
                      onChange={(event) => setRef(event.target.value.toUpperCase())}
                      className="h-9 border-[#3c4f3d]/10"
                    />
                  </div>
                  <div>
                    <Label className="text-xs font-normal text-[#3c4f3d]/70">Alternate Allele</Label>
                    <Input
                      type="text"
                      maxLength={1}
                      value={alt}
                      onChange={(event) => setAlt(event.target.value.toUpperCase())}
                      className="h-9 border-[#3c4f3d]/10"
                    />
                  </div>
                  <div>
                    <Label className="text-xs font-normal text-[#3c4f3d]/70">Orientation</Label>
                    <Select value={orientation} onValueChange={setOrientation}>
                      <SelectTrigger className="h-9 border-[#3c4f3d]/10">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="both">Forward + reverse-complement</SelectItem>
                        <SelectItem value="forward">Forward only</SelectItem>
                        <SelectItem value="reverse">Reverse-complement only</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="mt-6 flex flex-wrap gap-3">
                  <Button
                    onClick={handleSubmit}
                    disabled={isLoading}
                    className="bg-[#3c4f3d] text-white hover:bg-[#3c4f3d]/90"
                  >
                    {isLoading ? "Requesting raw signal..." : "Request raw signal"}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={loadExample}
                    className="border-[#3c4f3d]/10"
                  >
                    Load canonical input example
                  </Button>
                </div>

                {error && (
                  <Alert variant="destructive" className="mt-4">
                    <AlertCircle className="h-4 w-4" aria-hidden="true" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>

            {result ? (
              <Card className="gap-0 border-none bg-white py-0 shadow-sm">
                <CardHeader className="pt-5 pb-3">
                  <CardTitle className="text-base font-normal text-[#3c4f3d]">
                    Registered response fields
                  </CardTitle>
                  <CardDescription className="text-sm text-[#3c4f3d]/65">
                    These are raw scorer/provenance fields. No clinical label is derived here.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-5 pb-6">
                  <dl className="grid grid-cols-2 gap-x-5 gap-y-4 md:grid-cols-5">
                    <div>
                      <dt className="text-xs text-[#3c4f3d]/55">Normalized variant</dt>
                      <dd className="mt-1 break-all text-sm font-medium text-[#3c4f3d]">
                        {result.normalized_variant_id}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs text-[#3c4f3d]/55">Assembly</dt>
                      <dd className="mt-1 text-sm font-medium text-[#3c4f3d]">{result.assembly}</dd>
                    </div>
                    <div>
                      <dt className="text-xs text-[#3c4f3d]/55">Context</dt>
                      <dd className="mt-1 text-sm font-medium text-[#3c4f3d]">
                        {result.provenance.context_length_bp} bp
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs text-[#3c4f3d]/55">Status</dt>
                      <dd className="mt-1 text-sm font-medium text-[#3c4f3d]">{result.status}</dd>
                    </div>
                    <div>
                      <dt className="text-xs text-[#3c4f3d]/55">Research-only</dt>
                      <dd className="mt-1 text-sm font-medium text-[#3c4f3d]">
                        {result.provenance.research_only ? "Yes" : "No"}
                      </dd>
                    </div>
                  </dl>

                  <div>
                    <h3 className="text-xs uppercase tracking-[0.12em] text-[#3c4f3d]/50">Model signals</h3>
                    <div className="mt-2 overflow-x-auto rounded-md border border-[#3c4f3d]/10">
                      <table className="w-full min-w-[620px] text-left text-sm">
                        <thead className="bg-[#f7f9f7] text-xs text-[#3c4f3d]/60">
                          <tr>
                            <th className="px-3 py-2 font-medium">Scorer</th>
                            <th className="px-3 py-2 font-medium">Reference raw score</th>
                            <th className="px-3 py-2 font-medium">Alternate raw score</th>
                            <th className="px-3 py-2 font-medium">Primary delta</th>
                            <th className="px-3 py-2 font-medium">FWD / RC delta</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr className="border-t border-[#3c4f3d]/10 text-[#3c4f3d]">
                            <td className="px-3 py-3">{result.provenance.scorer} v{result.provenance.scorer_version}</td>
                            <td className="px-3 py-3">{result.reference_score.toFixed(4)}</td>
                            <td className="px-3 py-3">{result.alternate_score.toFixed(4)}</td>
                            <td className="px-3 py-3 text-[#de8246]">{result.delta_primary.toFixed(4)}</td>
                            <td className="px-3 py-3">
                              {result.delta_forward?.toFixed(4) ?? "N/A"} / {result.delta_reverse?.toFixed(4) ?? "N/A"}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <dl className="grid gap-4 border-t border-[#3c4f3d]/10 pt-4 md:grid-cols-3">
                    <div>
                      <dt className="text-xs text-[#3c4f3d]/55">Calibrated study probability</dt>
                      <dd className="mt-1 text-sm text-[#3c4f3d]/70">Not available: no validation-frozen calibrator is registered.</dd>
                    </div>
                    <div>
                      <dt className="text-xs text-[#3c4f3d]/55">Uncertainty / abstention</dt>
                      <dd className="mt-1 text-sm text-[#3c4f3d]/70">Not available: no calibration artifact is registered.</dd>
                    </div>
                    <div>
                      <dt className="text-xs text-[#3c4f3d]/55">Comparator evidence</dt>
                      <dd className="mt-1 text-sm text-[#3c4f3d]/70">Not available: multi-model benchmark is blocked.</dd>
                    </div>
                  </dl>

                  <p className="rounded-md bg-[#e9eeea]/60 p-3 text-xs leading-5 text-[#3c4f3d]/65">
                    Provenance: {result.provenance.orientation_requested} orientation · {result.provenance.context_length_bp} bp context · raw research signal only.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="rounded-lg border border-dashed border-[#3c4f3d]/20 bg-white/60 p-5 text-sm text-[#3c4f3d]/65">
                No response loaded. A configured research scoring service is required; the
                default environment fails closed instead of using a fake scorer.
              </div>
            )}
          </TabsContent>

          {nonInteractiveAreas.map((area) => (
            <TabsContent key={area.id} value={area.id}>
              <EmptyAreaPanel area={area} />
            </TabsContent>
          ))}

          <TabsContent value="methods-provenance" className="space-y-6">
            <Card className="gap-0 border-none bg-white py-0 shadow-sm">
              <CardHeader className="pt-5 pb-3">
                <CardTitle className="text-base font-normal text-[#3c4f3d]">
                  Methods & Provenance
                </CardTitle>
                <CardDescription className="text-sm text-[#3c4f3d]/65">
                  The protocol endpoint is the source for runtime identity fields shown here.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6 pb-6">
                {protocol ? (
                  <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {[
                      ["Protocol version", protocol.protocol_version],
                      ["ML extension version", protocol.ml_extension_protocol_version],
                      ["Frozen at", protocol.frozen_at],
                      ["Identity", protocol.identity],
                      ["Context length", `${protocol.context_length_bp} bp`],
                      ["Research-only", protocol.research_only ? "Yes" : "No"],
                    ].map(([label, value]) => (
                      <div key={label}>
                        <dt className="text-xs text-[#3c4f3d]/55">{label}</dt>
                        <dd className="mt-1 text-sm font-medium text-[#3c4f3d]">{value}</dd>
                      </div>
                    ))}
                  </dl>
                ) : (
                  <Button
                    variant="outline"
                    onClick={handleLoadProtocol}
                    className="border-[#3c4f3d]/10"
                  >
                    Load protocol metadata
                  </Button>
                )}

                <div className="border-t border-[#3c4f3d]/10 pt-5">
                  <h3 className="text-xs font-medium uppercase tracking-[0.12em] text-[#3c4f3d]/55">
                    Frozen contract boundaries
                  </h3>
                  <ul className="mt-3 space-y-2 text-sm leading-6 text-[#3c4f3d]/70">
                    <li>• Temporal generalization is the ML-extension estimand.</li>
                    <li>• GRCh38 and the protocol-served context length define canonical input.</li>
                    <li>• Forward and reverse-complement raw signals are retained when requested.</li>
                    <li>• Calibration, clinical interpretation, and classification require registered artifacts.</li>
                    <li>• Missing model, compute, or registry evidence is surfaced as blocked.</li>
                  </ul>
                </div>

                {protocol && (
                  <p className="rounded-md bg-[#e9eeea]/60 p-3 text-xs leading-5 text-[#3c4f3d]/65">
                    Classification boundary: {protocol.classification_logic}
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
