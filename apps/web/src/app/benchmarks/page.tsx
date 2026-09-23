"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ArrowUpRight, BookOpen, ExternalLink, ShieldCheck } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "~/components/ui/tabs";
import { asNumber, asRecord, asString, type BenchmarkEntry, type BenchmarkFigure, type BenchmarkManifest, type BenchmarkStatus } from "~/lib/benchmarks/schema";
import { loadBenchmarkManifest } from "~/lib/benchmarks/load";

function statusClass(status: BenchmarkStatus): string {
  if (status === "PASS") return "bg-[#e2f2e5] text-[#27633d]";
  if (status === "COMPLETED_WITH_LIMITATIONS") return "bg-[#fff0df] text-[#9a551f]";
  if (status === "NOT_APPLICABLE") return "bg-[#eef0ed] text-[#60766b]";
  return "bg-[#fff1ee] text-[#a64535]";
}

function StatusPill({ status }: { status: BenchmarkStatus }) {
  return (
    <span className={`inline-flex rounded-full px-2.5 py-1 text-[11px] font-medium tracking-wide ${statusClass(status)}`}>
      {status.replaceAll("_", " ")}
    </span>
  );
}

function formatValue(value: number | string | null): string {
  if (value === null) return "Unavailable";
  if (typeof value === "string") return value;
  if (Number.isInteger(value)) return value.toLocaleString();
  return value.toFixed(4);
}

function metricRecord(value: unknown): Record<string, unknown> {
  const record = asRecord(value);
  return asRecord(record.locally_recomputed_metrics ?? record.metrics ?? record);
}

function metricLabel(key: string): string {
  return key
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function groupRows(value: unknown): Array<{ name: string; n: number | null; status: string; metrics: Record<string, unknown> }> {
  const groups = asRecord(asRecord(value).groups);
  return Object.entries(groups).map(([name, raw]) => {
    const group = asRecord(raw);
    return {
      name,
      n: asNumber(group.n),
      status: asString(group.status) ?? "UNAVAILABLE",
      metrics: asRecord(group.metrics),
    };
  });
}

function figureMatches(figure: BenchmarkFigure, ids: string[]): boolean {
  const figureIds = figure.benchmark_id.split("-");
  return ids.some((id) => figureIds.includes(id) || figure.benchmark_id === id);
}

function FigureStrip({ figures, benchmarkIds }: { figures: BenchmarkFigure[]; benchmarkIds: string[] }) {
  const selected = figures.filter((figure) => figureMatches(figure, benchmarkIds));
  if (!selected.length) return null;
  return (
    <div className="mt-6 grid gap-4 lg:grid-cols-2" aria-label="Benchmark figures">
      {selected.map((figure) => (
        <figure key={figure.id} className="overflow-hidden border border-[#274238]/10 bg-white">
          <Image
            src={figure.asset}
            alt={`${figure.title}; ${figure.population}; n=${figure.n ?? "not available"}`}
            width={800}
            height={450}
            className="h-auto w-full"
            loading="lazy"
          />
          <figcaption className="border-t border-[#274238]/10 px-4 py-3 text-xs leading-5 text-[#60766b]">
            <span className="font-medium text-[#274238]">{figure.title}</span> · {figure.population} · n={figure.n ?? "N/A"} · <a className="underline underline-offset-2" href={figure.source_data}>source data</a>
          </figcaption>
        </figure>
      ))}
    </div>
  );
}

function Panel({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return (
    <section className="border border-[#274238]/10 bg-white" aria-labelledby={`${title.toLowerCase().replaceAll(" ", "-")}-heading`}>
      <div className="border-b border-[#274238]/10 px-5 py-5 sm:px-6">
        <h2 id={`${title.toLowerCase().replaceAll(" ", "-")}-heading`} className="text-lg font-medium text-[#274238]">{title}</h2>
        {description ? <p className="mt-1 max-w-3xl text-sm leading-6 text-[#60766b]">{description}</p> : null}
      </div>
      <div className="px-5 py-5 sm:px-6">{children}</div>
    </section>
  );
}

function BenchmarkLedger({ entries }: { entries: BenchmarkEntry[] }) {
  return (
    <div className="divide-y divide-[#274238]/10 border-y border-[#274238]/10">
      {entries.map((entry) => (
        <div key={entry.id} className="grid gap-3 py-4 md:grid-cols-[70px_minmax(0,1fr)_180px] md:items-start">
          <span className="font-mono text-xs font-medium text-[#de8246]">{entry.id}</span>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-sm font-medium text-[#274238]">{entry.title}</h3>
              <StatusPill status={entry.status} />
            </div>
            <p className="mt-1 text-sm leading-6 text-[#60766b]">{entry.summary}</p>
          </div>
          <div className="text-xs leading-5 text-[#60766b] md:text-right">
            <div>{entry.population}</div>
            <div className="font-mono">n={entry.n ?? "N/A"}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function MetricTable({ metrics }: { metrics: Record<string, unknown> }) {
  const rows = Object.entries(metrics).filter(([, value]) => typeof value === "number");
  return (
    <div className="grid gap-x-8 gap-y-3 sm:grid-cols-2">
      {rows.map(([key, value]) => (
        <div key={key} className="flex items-baseline justify-between gap-4 border-b border-[#274238]/10 pb-2">
          <span className="text-sm text-[#60766b]">{metricLabel(key)}</span>
          <span className="font-mono text-sm tabular-nums text-[#274238]">{formatValue(value as number)}</span>
        </div>
      ))}
    </div>
  );
}

function GroupTable({ value, metric = "auroc" }: { value: unknown; metric?: string }) {
  const rows = groupRows(value);
  if (!rows.length) return <p className="text-sm text-[#60766b]">No subgroup rows are available.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[520px] text-left text-sm">
        <caption className="sr-only">Benchmark subgroup metrics</caption>
        <thead className="border-b border-[#274238]/15 text-xs uppercase tracking-[0.12em] text-[#60766b]">
          <tr><th className="pb-3 pr-4 font-medium">Group</th><th className="pb-3 pr-4 font-medium">n</th><th className="pb-3 pr-4 font-medium">Status</th><th className="pb-3 font-medium">{metricLabel(metric)}</th></tr>
        </thead>
        <tbody className="divide-y divide-[#274238]/10">
          {rows.map((row) => (
            <tr key={row.name}>
              <td className="py-3 pr-4 font-medium text-[#274238]">{row.name}</td>
              <td className="py-3 pr-4 font-mono text-[#60766b]">{row.n ?? "N/A"}</td>
              <td className="py-3 pr-4 text-xs text-[#60766b]">{row.status.replaceAll("_", " ")}</td>
              <td className="py-3 font-mono text-[#274238]">{formatValue(asNumber(row.metrics[metric]))}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function OverviewTab({ manifest }: { manifest: BenchmarkManifest }) {
  const statusCounts = manifest.benchmarks.reduce<Record<BenchmarkStatus, number>>((counts, entry) => {
    counts[entry.status] += 1;
    return counts;
  }, { PASS: 0, COMPLETED_WITH_LIMITATIONS: 0, NOT_APPLICABLE: 0, DATA_BLOCKED: 0, COMPUTE_BLOCKED: 0 });
  return (
    <div className="space-y-6">
      <Panel title="Registry status" description="All B01-B68 entries stay visible, including work that is not applicable, data-blocked, or compute-blocked.">
        <div className="grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-5">
          {(["PASS", "COMPLETED_WITH_LIMITATIONS", "NOT_APPLICABLE", "DATA_BLOCKED", "COMPUTE_BLOCKED"] as const).map((status) => <div key={status}><p className="text-xs uppercase tracking-[0.1em] text-[#60766b]">{status.replaceAll("_", " ")}</p><p className="mt-2 font-mono text-2xl text-[#274238]">{statusCounts[status]}</p></div>)}
        </div>
        <p className="mt-5 border-t border-[#274238]/10 pt-4 text-sm text-[#60766b]">Total benchmark entries: <span className="font-mono text-[#274238]">{manifest.benchmarks.length}</span></p>
      </Panel>
      <Panel title="What we contributed" description="A judge can trace the contribution from the headline to the exact benchmark entry, source artifact, figure, or explicit limitation.">
        <div className="grid gap-x-8 gap-y-2 md:grid-cols-2">
          {manifest.what_we_contributed.map((item) => (
            <div key={item.benchmark_id} className="flex items-start gap-3 border-b border-[#274238]/10 py-3">
              <span className="mt-0.5 font-mono text-xs text-[#de8246]">{item.benchmark_id}</span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-medium text-[#274238]">{item.title}</span>
                  <StatusPill status={item.status} />
                </div>
                <p className="mt-1 text-xs text-[#60766b]">{item.web_tab}</p>
              </div>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="The registry is the interface" description="The hub is generated from one canonical B01-B68 registry. PASS means persisted evidence exists; limitations and blocked work remain visible.">
        <BenchmarkLedger entries={manifest.benchmarks} />
      </Panel>
    </div>
  );
}

function BaselineTab({ manifest }: { manifest: BenchmarkManifest }) {
  const primary = metricRecord(manifest.data.primary);
  return (
    <div className="space-y-6">
      <Panel title="Primary frozen temporal result" description="The 946-row locked cohort is immutable. Values below are read from the registered artifact and locally checked within 1e-9; this page does not retune or refit it.">
        <div className="mb-6 flex flex-wrap items-center gap-3"><StatusPill status="PASS" /><span className="text-sm text-[#60766b]">higher is more pathogenic · calibrated threshold 0.50 · 946 locked variants</span></div>
        <MetricTable metrics={primary} />
        <FigureStrip figures={manifest.figures} benchmarkIds={["B35", "B36", "B37", "B38", "B39"]} />
      </Panel>
      <Panel title="Stage boundary" description="Development, frozen temporal evaluation, and external manifest construction are separate evidence stages.">
        <div className="grid gap-4 sm:grid-cols-3">
          {[["Development", "4,000", "TRAIN + VALIDATION"], ["Locked temporal", "946", "one-shot frozen evaluation"], ["External manifest", formatValue(manifest.headline_cards.find((card) => card.id === "external_n")?.value ?? null), "scores blocked"]].map(([label, value, detail]) => (
            <div key={label} className="border-l-2 border-[#de8246]/60 pl-4"><p className="text-xs uppercase tracking-[0.12em] text-[#60766b]">{label}</p><p className="mt-2 font-mono text-2xl text-[#274238]">{value}</p><p className="mt-1 text-xs text-[#60766b]">{detail}</p></div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

function ComparisonTab({ manifest }: { manifest: BenchmarkManifest }) {
  const entries = manifest.benchmarks.filter((entry) => entry.web_tab === "Model Comparison");
  return <div className="space-y-6"><Panel title="Model comparison" description="Evo2, Nucleotide Transformer, Caduceus, CADD, and PhyloP remain stage-qualified. Coverage is shown next to performance rather than hidden in a footnote."><BenchmarkLedger entries={entries} /><FigureStrip figures={manifest.figures} benchmarkIds={entries.map((entry) => entry.id).concat(["B55"])} /></Panel></div>;
}

function HpoTab({ manifest }: { manifest: BenchmarkManifest }) {
  return <Panel title="HPO & training" description="Downstream HPO and learning-curve evidence is separate from the incomplete foundation-model adaptation study."><BenchmarkLedger entries={manifest.benchmarks.filter((entry) => entry.web_tab === "HPO & Training")} /><FigureStrip figures={manifest.figures} benchmarkIds={["B22", "B23", "B31"]} /></Panel>;
}

function CalibrationTab({ manifest }: { manifest: BenchmarkManifest }) {
  const data = manifest.data;
  return <div className="space-y-6"><Panel title="Calibration & uncertainty" description="Frozen probabilities, confidence strata, abstention, threshold sensitivity, and per-model validation metrics are descriptive and stage-labeled."><MetricTable metrics={metricRecord(data.primary)} /><div className="mt-6"><h3 className="mb-3 text-sm font-medium text-[#274238]">Confidence strata</h3><GroupTable value={data.confidence} /></div><div className="mt-6"><h3 className="mb-3 text-sm font-medium text-[#274238]">Threshold sensitivity</h3><MetricTable metrics={asRecord(data.threshold_sensitivity)} /></div><FigureStrip figures={manifest.figures} benchmarkIds={["B26", "B27", "B28", "B29", "B30", "B51", "B56"]} /></Panel><Panel title="Related registry entries"><BenchmarkLedger entries={manifest.benchmarks.filter((entry) => entry.web_tab === "Calibration & Uncertainty")} /></Panel></div>;
}

function GeneralizationTab({ manifest }: { manifest: BenchmarkManifest }) {
  const loco = asRecord(manifest.data.loco);
  const seed = asRecord(manifest.data.seed_robustness);
  return <div className="space-y-6"><Panel title="Generalization" description="Chromosome-held-out fits use cached formal features only. Seed robustness is downstream MLP variation, not foundation-model fine-tuning."><div className="grid gap-6 md:grid-cols-2"><div><h3 className="mb-3 text-sm font-medium text-[#274238]">Leave-one-chromosome-out</h3><p className="text-sm leading-6 text-[#60766b]">{asNumber(loco.completed_chromosomes) ?? 0} of {asNumber(loco.chromosome_count) ?? 0} chromosome groups have sufficient support for metrics.</p></div><div><h3 className="mb-3 text-sm font-medium text-[#274238]">Seed robustness</h3><p className="text-sm leading-6 text-[#60766b]">AUROC range: <span className="font-mono text-[#274238]">{formatValue(asNumber(seed.auroc_range))}</span></p></div></div><FigureStrip figures={manifest.figures} benchmarkIds={["B42", "B48", "B57"]} /></Panel><Panel title="Generalization registry entries"><BenchmarkLedger entries={manifest.benchmarks.filter((entry) => entry.web_tab === "Generalization")} /></Panel></div>;
}

function EvidenceTab({ manifest }: { manifest: BenchmarkManifest }) {
  return <div className="space-y-6"><Panel title="Evidence quality" description="ClinVar review-status stars are evidence-quality strata, not a claim that the underlying biology is certain."><GroupTable value={manifest.data.evidence_quality} /><FigureStrip figures={manifest.figures} benchmarkIds={["B46"]} /></Panel><Panel title="Evidence-quality registry entries"><BenchmarkLedger entries={manifest.benchmarks.filter((entry) => entry.web_tab === "Evidence Quality")} /></Panel></div>;
}

function TemporalTab({ manifest }: { manifest: BenchmarkManifest }) {
  return <div className="space-y-6"><Panel title="Temporal difficulty" description="Time-to-resolution bins use T0/T1 ClinVar LastEvaluated dates. The association is exploratory; missing and invalid dates remain visible."><GroupTable value={manifest.data.temporal_difficulty} /><FigureStrip figures={manifest.figures} benchmarkIds={["B47", "B68"]} /></Panel><Panel title="Temporal registry entries"><BenchmarkLedger entries={manifest.benchmarks.filter((entry) => entry.web_tab === "Temporal Difficulty")} /></Panel></div>;
}

function DisagreementTab({ manifest }: { manifest: BenchmarkManifest }) {
  const data = asRecord(manifest.data.disagreement);
  const counts = asRecord(data.category_counts);
  return <div className="space-y-6"><Panel title="Model disagreement" description="Common validation rows show where foundation and classical evidence agrees or diverges. Consensus is not treated as truth; it is a way to locate hard cases."><div className="grid gap-3 sm:grid-cols-3">{Object.entries(counts).map(([key, value]) => <div key={key} className="border-b border-[#274238]/10 pb-3"><p className="text-xs uppercase tracking-[0.12em] text-[#60766b]">{key}</p><p className="mt-2 font-mono text-2xl text-[#274238]">{formatValue(asNumber(value))}</p></div>)}</div><p className="mt-5 text-sm text-[#60766b]">Common validation rows: <span className="font-mono text-[#274238]">{formatValue(asNumber(data.n_common_validation))}</span>. Foundation-versus-classical disagreements: <span className="font-mono text-[#274238]">{formatValue(asNumber(data.foundation_vs_classical_disagreement_n))}</span>.</p><FigureStrip figures={manifest.figures} benchmarkIds={["B49", "B52"]} /></Panel><Panel title="Disagreement registry entries"><BenchmarkLedger entries={manifest.benchmarks.filter((entry) => entry.web_tab === "Model Disagreement")} /></Panel></div>;
}

function ExternalTab({ manifest }: { manifest: BenchmarkManifest }) {
  const external = asRecord(manifest.data.external);
  return <div className="space-y-6"><Panel title="External benchmarks" description="The candidate manifest is frozen before inference. No external performance is shown while balance and reference-data gates are unresolved."><div className="grid gap-5 md:grid-cols-[1fr_auto]"><div><p className="text-sm leading-6 text-[#60766b]">Selected candidates: <span className="font-mono text-[#274238]">{formatValue(asNumber(external.selected_n))}</span>. The selection excludes formal and locked IDs and genes and requires review stars at least 2.</p><p className="mt-3 text-sm leading-6 text-[#a64535]">Inference status: {asString(external.inference_status) ?? "COMPUTE_BLOCKED"}. Reference: {asString(external.reference_status) ?? "DATA_BLOCKED"}.</p></div><StatusPill status="COMPUTE_BLOCKED" /></div><FigureStrip figures={manifest.figures} benchmarkIds={["B61", "B62", "B63", "B64", "B65", "B66", "B67"]} /></Panel><Panel title="External registry entries"><BenchmarkLedger entries={manifest.benchmarks.filter((entry) => entry.web_tab === "External Benchmarks")} /></Panel></div>;
}

function CasesTab({ manifest }: { manifest: BenchmarkManifest }) {
  const cases = Array.isArray(manifest.data.case_studies) ? manifest.data.case_studies : [];
  return <div className="space-y-6"><Panel title="Errors & case studies" description="Deterministic examples are selected from the immutable locked artifact. They are research evidence, not patient-facing recommendations."><div className="grid gap-4 md:grid-cols-2">{cases.map((raw, index) => { const item = asRecord(raw); const caseId = asString(item.case_id) ?? `case-${index + 1}`; return <article key={caseId} className="border border-[#274238]/10 p-4"><div className="flex items-center justify-between gap-3"><span className="font-mono text-xs text-[#de8246]">{caseId}</span><span className="text-xs text-[#60766b]">{asString(item.reason) ?? "deterministic case"}</span></div><h3 className="mt-3 text-base font-medium text-[#274238]">{asString(item.normalized_variant_id) ?? "Variant ID unavailable"}</h3><dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-xs"><dt className="text-[#60766b]">Gene</dt><dd className="text-right text-[#274238]">{asString(item.gene_symbol) ?? "N/A"}</dd><dt className="text-[#60766b]">Label</dt><dd className="text-right text-[#274238]">{formatValue(asNumber(item.label))}</dd><dt className="text-[#60766b]">Calibrated score</dt><dd className="text-right font-mono text-[#274238]">{formatValue(asNumber(item.calibrated_score))}</dd><dt className="text-[#60766b]">Review stars</dt><dd className="text-right text-[#274238]">{formatValue(asNumber(item.review_stars))}</dd></dl></article>; })}</div><FigureStrip figures={manifest.figures} benchmarkIds={["B40", "B41", "B50"]} /></Panel><Panel title="Case-study registry entries"><BenchmarkLedger entries={manifest.benchmarks.filter((entry) => entry.web_tab === "Errors & Case Studies")} /></Panel></div>;
}

function RuntimeTab({ manifest }: { manifest: BenchmarkManifest }) {
  const entry = manifest.benchmarks.find((item) => item.id === "B45");
  const compute = asRecord(manifest.data.compute);
  return <div className="space-y-6"><Panel title="Runtime & cost" description="Historical compute evidence and cache reuse are distinct from new expansion spend. The expansion launched no Modal resources."><div className="grid gap-5 sm:grid-cols-3"><div><p className="text-xs uppercase tracking-[0.12em] text-[#60766b]">New spend</p><p className="mt-2 font-mono text-2xl text-[#274238]">${formatValue(asNumber(compute.new_spend_usd))}</p></div><div><p className="text-xs uppercase tracking-[0.12em] text-[#60766b]">Modal resources</p><p className="mt-2 text-sm text-[#274238]">{formatValue(asNumber(compute.resources_started))}</p></div><div><p className="text-xs uppercase tracking-[0.12em] text-[#60766b]">Balance gate</p><p className="mt-2 text-sm text-[#a64535]">{asString(compute.balance_status) ?? "Unavailable"}</p></div></div><FigureStrip figures={manifest.figures} benchmarkIds={["B43", "B44", "B45"]} /></Panel>{entry ? <Panel title="Cost limitation"><BenchmarkLedger entries={[entry]} /></Panel> : null}</div>;
}

function FineTuningTab({ manifest }: { manifest: BenchmarkManifest }) {
  const fineTuning = manifest.fine_tuning;
  const checks: Array<[string, unknown]> = [["Foundation-model fine-tuning in primary result", fineTuning.foundation_model_fine_tuning_in_primary_result], ["Fine-tuning implementation built", fineTuning.fine_tuning_implementation_built], ["Real encoder-update feasibility proof", fineTuning.real_encoder_update_feasibility_proof], ["Complete fine-tuned benchmark study", fineTuning.complete_fine_tuned_benchmark_study]];
  return <div className="space-y-6"><Panel title="Fine-tuning attempt" description="This boundary is intentionally explicit: feasibility evidence is not presented as a completed scientific benchmark."><div className="grid gap-3 md:grid-cols-2">{checks.map(([label, value]) => <div key={label} className="border-b border-[#274238]/10 py-3"><p className="text-xs uppercase tracking-[0.1em] text-[#60766b]">{label}</p><p className="mt-2 text-sm font-medium text-[#274238]">{asString(value) ?? "Unavailable"}</p></div>)}</div><p className="mt-5 max-w-3xl text-sm leading-6 text-[#60766b]">{asString(fineTuning.limitation) ?? "Existing feasibility evidence is not a complete fine-tuned scientific result."}</p><div className="mt-5 flex flex-wrap gap-3">{["/benchmarks/downloads/EvoVariant_TR_FineTuning_Attempt_Demo.ipynb", "/benchmarks/downloads/encoder_update_proof.json"].map((href) => <a key={href} href={href} className="inline-flex items-center gap-2 border border-[#274238]/15 px-3 py-2 text-sm text-[#274238] underline-offset-2 hover:bg-[#e9eeea] hover:underline">{href.split("/").pop()} <ArrowUpRight className="h-3.5 w-3.5" aria-hidden="true" /></a>)}</div></Panel></div>;
}

function ReproducibilityTab({ manifest }: { manifest: BenchmarkManifest }) {
  return <div className="space-y-6"><Panel title="Reproducibility" description="Hashes and commands are generated with the benchmark manifest. Secrets and model weights are not published."><div className="divide-y divide-[#274238]/10">{Object.entries(manifest.reproducibility).filter(([, value]) => typeof value === "string" || typeof value === "number").map(([key, value]) => <div key={key} className="grid gap-2 py-3 sm:grid-cols-[260px_minmax(0,1fr)]"><dt className="text-xs uppercase tracking-[0.1em] text-[#60766b]">{metricLabel(key)}</dt><dd className="break-all font-mono text-xs text-[#274238]">{String(value)}</dd></div>)}</div><div className="mt-5"><h3 className="mb-3 text-sm font-medium text-[#274238]">Reproduction commands</h3><pre className="overflow-x-auto bg-[#274238] p-4 text-xs leading-6 text-[#f4f6f2]">{Array.isArray(manifest.reproducibility.commands) ? manifest.reproducibility.commands.join("\n") : "Commands unavailable"}</pre></div></Panel></div>;
}

function DownloadsTab({ manifest }: { manifest: BenchmarkManifest }) {
  return <Panel title="Downloads" description="Compact generated artifacts keep the judge path small: summaries, registry, protocol, methods, cases, notebooks, and figures."><ul className="divide-y divide-[#274238]/10">{manifest.downloads.map((download) => <li key={download.path} className="flex flex-wrap items-center justify-between gap-3 py-3"><span className="text-sm text-[#274238]">{download.label}</span><a href={download.path} className="inline-flex items-center gap-2 text-sm text-[#de8246] underline underline-offset-2">Download <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" /></a></li>)}</ul></Panel>;
}

function TabBody({ label, manifest }: { label: string; manifest: BenchmarkManifest }) {
  if (label === "Overview") return <OverviewTab manifest={manifest} />;
  if (label === "Core Baseline") return <BaselineTab manifest={manifest} />;
  if (label === "Model Comparison") return <ComparisonTab manifest={manifest} />;
  if (label === "HPO & Training") return <HpoTab manifest={manifest} />;
  if (label === "Calibration & Uncertainty") return <CalibrationTab manifest={manifest} />;
  if (label === "Generalization") return <GeneralizationTab manifest={manifest} />;
  if (label === "Evidence Quality") return <EvidenceTab manifest={manifest} />;
  if (label === "Temporal Difficulty") return <TemporalTab manifest={manifest} />;
  if (label === "Model Disagreement") return <DisagreementTab manifest={manifest} />;
  if (label === "External Benchmarks") return <ExternalTab manifest={manifest} />;
  if (label === "Errors & Case Studies") return <CasesTab manifest={manifest} />;
  if (label === "Runtime & Cost") return <RuntimeTab manifest={manifest} />;
  if (label === "Fine-Tuning Attempt") return <FineTuningTab manifest={manifest} />;
  if (label === "Reproducibility") return <ReproducibilityTab manifest={manifest} />;
  return <DownloadsTab manifest={manifest} />;
}

export default function BenchmarksPage() {
  const [manifest, setManifest] = useState<BenchmarkManifest | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    void loadBenchmarkManifest(controller.signal).then(setManifest).catch((requestError: unknown) => {
      if (requestError instanceof DOMException && requestError.name === "AbortError") return;
      setError(requestError instanceof Error ? requestError.message : "Benchmark manifest is unavailable");
    });
    return () => controller.abort();
  }, []);

  const tabs = useMemo(() => manifest?.tabs ?? [], [manifest]);

  return (
    <div className="min-h-screen bg-[#e9eeea] text-[#274238]">
      <header className="border-b border-[#274238]/10 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-5 py-4 sm:px-8">
          <div className="flex items-center gap-3">
            <div className="relative"><span className="text-xl font-light tracking-wide text-[#274238]">EVO<span className="text-[#de8246]">2</span></span><span className="absolute -bottom-1 left-0 h-0.5 w-12 bg-[#de8246]" /></div>
            <span className="text-sm text-[#60766b]">Variant Analysis</span>
          </div>
          <nav aria-label="Primary" className="flex items-center gap-1 text-sm">
            <Link href="/" className="rounded-md px-3 py-2 text-[#60766b] hover:bg-[#e9eeea] hover:text-[#274238]">Variant analysis</Link>
            <Link href="/analysis" className="rounded-md px-3 py-2 text-[#60766b] hover:bg-[#e9eeea] hover:text-[#274238]">Research workbench</Link>
            <Link href="/benchmarks" aria-current="page" className="rounded-md bg-[#274238] px-3 py-2 text-white">Benchmarks</Link>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-5 py-8 sm:px-8 sm:py-12">
        <section className="grid gap-8 border-b border-[#274238]/15 pb-10 lg:grid-cols-[minmax(0,1fr)_320px] lg:items-end">
          <div>
            <div className="mb-5 flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-[#de8246]"><ShieldCheck className="h-4 w-4" aria-hidden="true" /> Research evidence hub</div>
            <h1 className="max-w-4xl text-4xl font-light leading-[1.08] tracking-[-0.03em] text-[#274238] sm:text-6xl">{manifest?.title ?? "EvoVariant-TR Research Benchmarks"}</h1>
            <p className="mt-5 max-w-3xl text-base leading-7 text-[#60766b]">{manifest?.subtitle ?? "Temporal evaluation, model comparison, generalization, calibration, uncertainty, robustness, external validation, compute, and reproducibility."}</p>
          </div>
          <div className="border-l-2 border-[#de8246]/70 pl-5 text-sm leading-6 text-[#60766b]"><p className="font-medium text-[#274238]">Research-only surface</p><p className="mt-2">The primary temporal result is frozen. Every extension below carries its population, stage, source, and limitation.</p></div>
        </section>

        {error ? <div role="alert" className="mt-8 border border-[#a64535]/20 bg-[#fff1ee] px-5 py-4 text-sm text-[#a64535]">{error}. Confirm the generated public benchmark manifest exists, then reload.</div> : null}

        {manifest ? <>
          <dl className="mt-8 grid grid-cols-2 border-y border-[#274238]/15 sm:grid-cols-4 lg:grid-cols-7">
            {manifest.headline_cards.map((card) => <div key={card.id} className="border-r border-[#274238]/10 px-3 py-4 first:pl-0 last:border-r-0 sm:px-4"><dt className="text-[11px] uppercase leading-4 tracking-[0.1em] text-[#60766b]">{card.label}</dt><dd className="mt-2 font-mono text-xl tabular-nums text-[#274238]">{formatValue(card.value)}</dd><dd className="mt-1 text-[11px] text-[#60766b]">{card.source}</dd></div>)}
          </dl>

          <section className="mt-8" aria-labelledby="benchmark-navigation-heading">
            <div className="mb-3 flex items-center gap-2"><BookOpen className="h-4 w-4 text-[#de8246]" aria-hidden="true" /><h2 id="benchmark-navigation-heading" className="text-sm font-medium text-[#274238]">Explore the evidence</h2></div>
            <Tabs defaultValue={tabs[0]?.id ?? "overview"} className="gap-6">
              <div className="w-full overflow-x-auto pb-1"><TabsList className="min-w-max bg-white p-1" aria-label="Benchmark sections">{tabs.map((tab) => <TabsTrigger key={tab.id} value={tab.id} className="data-[state=active]:bg-[#274238] data-[state=active]:text-white">{tab.label}</TabsTrigger>)}</TabsList></div>
              {tabs.map((tab) => <TabsContent key={tab.id} value={tab.id}><TabBody label={tab.label} manifest={manifest} /></TabsContent>)}
            </Tabs>
          </section>
        </> : <div className="mt-12 border border-[#274238]/10 bg-white px-6 py-10 text-sm text-[#60766b]">Loading the generated benchmark manifest…</div>}
      </main>
      <footer className="border-t border-[#274238]/10 bg-white"><div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-5 py-6 text-xs text-[#60766b] sm:px-8"><span>Evidence-gated temporal variant research · no clinical classification</span><Link href="/analysis" className="inline-flex items-center gap-1 text-[#274238] underline underline-offset-2">Open research workbench <ExternalLink className="h-3 w-3" aria-hidden="true" /></Link></div></footer>
    </div>
  );
}
