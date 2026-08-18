# LEGACY SCIENTIFIC AUDIT — EvoVariant source snapshot (Milestone 003)

Date: 2026-08-18
Evidence stage of all legacy metrics referenced below: **LEGACY_BASELINE_ONLY**.

This audit documents exactly what the supplied legacy code claims and where those
claims conflict with the EvoVariant-TR research protocol. Nothing here is accepted
as the new design. Companion machine-readable table: `docs/audit/HARDCODED_ASSUMPTIONS.csv`.

---

## 1. End-to-end request trace (frontend input → backend output)

1. **User** selects genome (default `hg38` in UI) and chromosome, searches a gene
   (e.g. BRCA1) via NCBI clinicaltables (`genome-api.ts:141`).
2. **GeneViewer** fetches gene bounds via NCBI eutils (`genome-api.ts:189`) and the
   gene sequence window via UCSC (`genome-api.ts:242`).
3. **ClinVar variants** for the gene region are fetched via NCBI eutils
   esearch/esummary `db=clinvar` (`genome-api.ts:278-313`).
4. **Variant submission**: user picks a position + alt base (A/C/G/T). The frontend
   POSTs `{variant_position, alternative, genome, chromosome}` to the Modal FastAPI
   endpoint (`NEXT_PUBLIC_ANALYZE_SINGLE_VARIANT_BASE_URL`).
5. **Backend** (`main.py:306 analyze_single_variant`):
   - `get_genome_sequence` fetches a window from **live UCSC** (`main.py:235`).
   - Computes `relative_pos = variant_position - 1 - seq_start` (`main.py:328`).
   - Extracts `reference = window_seq[relative_pos]` (`main.py:335`).
   - `analyze_variant` builds `var_seq` by single-base substitution, scores ref and
     alt with `model.score_sequences`, computes `delta = var - ref` (`main.py:260-267`).
   - Applies the **hard-coded BRCA1 threshold** and **confidence heuristic**
     (`main.py:269-278`) and returns
     `{reference, alternative, delta_score, prediction, classification_confidence, position}`.
6. **Frontend** renders `prediction` ("Likely pathogenic"/"Likely benign") and a
   `classification_confidence` bar; optionally compares against the ClinVar row.

---

## 2. Hard-coded scientific assumptions (full list)

See `HARDCODED_ASSUMPTIONS.csv` for the machine-readable table. Key items:

### 2.1 Decision threshold and confidence (BRCA1-derived)
- `threshold = -0.0009178519` (`main.py:269`)
- `lof_std = 0.0015140239` (`main.py:270`)
- `func_std = 0.0009016589` (`main.py:271`)
- Decision rule: `delta < threshold → "Likely pathogenic"`, else `"Likely benign"`.
- Confidence: `min(1, |delta - threshold| / std)` with class-specific std.

These constants were derived from a BRCA1 deep-mutational-scan subset (see §4).
They are a **single-gene, current-label, hg19** calibration. The new project's
primary design is a **genome-wide, temporal, GRCh38** benchmark with a frozen
orientation-aware score and calibration fit only on a disjoint definitive-at-t0
cohort. **These constants must not be inherited.**

### 2.2 Binary clinical-sounding labels
- `"Likely pathogenic"` / `"Likely benign"` strings (`main.py:274,277`) and the
  `classification_confidence` field are rendered by the UI as a clinical
  classification with a confidence bar. This conflicts with the claim-safety policy
  (master prompt §13) and the new evidence-stage model. **Banned from new default
  UI/API.**

### 2.3 Model identity
- `Evo2('evo2_7b')` loaded in two places (`main.py:57,301`). The checkpoint is
  referenced only by the string name `evo2_7b`; no pinned revision, no checksum, no
  official-package self-test. **Checkpoint identity must be re-established**
  (Milestones 49/51) before any scoring.

### 2.4 Genome assembly
- The serving endpoint accepts a `genome` parameter and the UI defaults to `hg38`,
  but the **threshold/BRCA1 analysis uses GRCh37/hg19** (`main.py:80`
  `GRCh37.p13_chr17.fna.gz`; evaluator default `--genome hg19`). The legacy system
  mixes assemblies. The new project is **GRCh38-only** for the primary cohort.

### 2.5 Window length
- `WINDOW_SIZE = 8192` is declared (`main.py:54,317`), but the actual window formula
  produces **8,193 bases** for interior positions (see §3). The intended 8,192-base
  contract is not actually enforced.

### 2.6 Endpoint / deployment identities
- Modal app name `variant-analysis-evo2` (`main.py:33`), volume `hf_cache`
  (`main.py:35`), and the old deployment URL
  `https://utkarshmer05--variant-analysis-evo2-evo2model-analyze-si-b52940.modal.run`
  (`evaluate_modal_endpoint.py:35`). **None may be silently reused** as final
  EvoVariant-TR infrastructure.

---

## 3. The 8,193-base window defect (must not be inherited)

`get_genome_sequence` (`main.py:224-257`):

```python
half_window = window_size // 2          # 4096
start = max(0, position - 1 - half_window)
end   = position - 1 + half_window + 1
```

For an ordinary interior position (far from the chromosome start), `max(0, ...)`
does not clamp, so:

```
end - start = (position - 1 + 4096 + 1) - (position - 1 - 4096) = 8193
```

The UCSC query therefore requests **8,193 bases**, and the returned `window_seq`
is 8,193 bases long, even though `WINDOW_SIZE` is declared as 8,192. The variant's
relative index (`main.py:328`) is computed against this 8,193-length window. This
is exactly the defect flagged in master prompt §1. The new project freezes a
correct even-window convention with hard assertions
(`end - start == 8192`, `len(seq) == 8192`, variant index fixed) at Milestones
33/41. **This formula is not reused.**

---

## 4. BRCA1-specific assumptions and threshold-selection leakage

`run_brca1_analysis` (`main.py:40-197`):

- Loads the **Findlay et al. 2018 BRCA1 saturation-editing** dataset
  (`41586_2018_461_MOESM3_ESM.xlsx`, header=2) and a **GRCh37 chr17** FASTA.
- Collapses classes to two: `LOF` vs `FUNC/INT` (`main.py:78`).
- Takes the **first 500 rows** (`brca1_df.iloc[:500]`, `main.py:93`).
- Scores ref/alt, computes delta, then derives the operating threshold by
  **ROC Youden-index argmax on the same 500 rows** (`main.py:136-140`) and the two
  std constants from the same rows' score distributions (`main.py:142-148`).

**Leakage:** the threshold and confidence constants are selected on the very rows
used to report performance. The saved 100-row evaluation
(`evaluation/results/final_100/`) then scores a **subset of the same BRCA1 rows**
(first 100 of the same xlsx) through the endpoint that already embeds those
constants. This is threshold selection on evaluation-overlapping labels — the exact
practice the new protocol forbids (master prompt §6: never use test outcomes to
choose threshold/calibrator). The legacy AUROC/accuracy are therefore
**LEGACY_BASELINE_ONLY** and cannot be cited as EvoVariant-TR evidence.

Additionally, the legacy evaluation is a **current-label** BRCA1 functional-assay
benchmark, not a **temporal VUS-resolution** benchmark. It answers a different
question than EvoVariant-TR's primary estimand.

---

## 5. Live network dependencies in the inference path

- **Backend inference** calls **UCSC live** per request (`main.py:235`) with no
  timeout, no retry, no provenance, and no frozen reference. Final scoring must use
  a frozen local GRCh38 FASTA (Milestones 31-32), not per-request network retrieval.
- **Frontend** makes direct browser calls to UCSC (genome/chromosome/sequence) and
  NCBI (gene search, gene details, ClinVar) — see `genome-api.ts`. These are
  browse/metadata conveniences, distinct from the frozen research data path.

---

## 6. Test/evaluation leakage and threshold selection summary

| Issue | Location | Why it violates the new protocol |
|---|---|---|
| Threshold derived on eval rows | `main.py:136-140` | Threshold chosen on labels overlapping the evaluation set |
| Confidence stds from same rows | `main.py:142-148` | Calibrator constants fit on evaluation-overlapping data |
| 100-row eval ⊂ 500-row threshold set | `evaluate_modal_endpoint.py` + `main.py:93` | Evaluation subset is contained in the threshold-derivation set |
| Current-label, not temporal | whole legacy design | Does not estimate the t0→t1 VUS-resolution estimand |
| hg19 threshold applied to hg38 requests | `main.py:269` vs UI default hg38 | Assembly mismatch between calibration and serving |

---

## 7. Why the saved BRCA1 evaluation is baseline engineering evidence only

The `evaluation/results/final_100/` outputs (accuracy 0.90, AUROC-from-delta 0.9309,
median latency 2.60 s, 100/100 calls) demonstrate only that:

- the old endpoint could be reached and return a response;
- the old request/response plumbing and latency behavior worked;
- the old BRCA1-threshold classifier reproduced a known current-label BRCA1 signal.

They do **not** demonstrate temporal generalization, GRCh38 correctness, genome-wide
coverage, calibration validity, or any EvoVariant-TR scientific claim. They are
labeled **LEGACY_BASELINE_ONLY** and are retained solely as an engineering baseline
to distinguish pre-existing failures from refactor-introduced failures (Milestone 6).

---

## 8. Conflicts with the EvoVariant-TR protocol (summary)

| Legacy behavior | EvoVariant-TR requirement | Resolution |
|---|---|---|
| BRCA1 fixed threshold | No test-label threshold tuning; disjoint calibration | Do not inherit; fit Platt on definitive-at-t0 cohort |
| "Likely pathogenic/benign" + confidence | Raw score + evidence-stage labels; no clinical class | Replace with research-only outputs |
| 8,193-base window | Exact 8,192-base even window with assertions | New window contract (M33/M41) |
| Live UCSC in inference | Frozen local GRCh38 FASTA | New reference layer (M31/M32) |
| hg19/hg38 mixing | GRCh38-only primary | GRCh38-only |
| Unpinned `evo2_7b` | Frozen, official-implementation-verified checkpoint | Re-establish identity (M49/M51) |
| Old Modal app/volume/URL | New unique deployment identity | New app/volume (M52+) |
| Current-label BRCA1 benchmark | Temporal t0→t1 VUS-resolution benchmark | New estimand (protocol, M11) |
