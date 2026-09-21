# ML-extension deviation log

This log applies only to `research/ml_extension/protocol.yaml`. It does not rewrite or
retroactively alter the original frozen zero-shot protocol in `research/protocol/`.

## ML-DEV-001 — Freeze the reproducible 946-record extension test cohort

- Date: 2026-09-21
- Evidence timestamp (UTC): 2026-09-21T06:35:32.341621+00:00
- Protocol version affected: 1.1.0
- Status: ACCEPTED for the ML-extension study only
- Search evidence: `artifacts/phase3_recovery_search_20260921.json`
- Reference evidence: `data/manifests/grch38.json` and `artifacts/reference/grch38_validation_20260921.json`
- Implementation commit: `36063e8e1b65ddf1653347a5705e89115e52f1d5` (final frozen-control baseline; initial recovery implementation: `dd29318`)

### What changed

The historical handoff recorded a validation-only target of 1,403,225 t0 VUS identities and a
1,024-variant temporal cohort with 614 B/LB and 410 P/LP outcomes. An exhaustive search of the
complete fetched Git history, all refs, branches, tags, reflog, unreachable objects, deleted
paths, repository artifacts, ignored/generated outputs, presentations, local worktrees, and
supplied attachments did not recover a frozen normalized-ID set or source-row manifest capable
of reconstructing those exact records.

The manifest-verified ClinVar archives and the deterministic current pipeline therefore become
the authoritative ML-extension source. They produce 1,402,895 unique t0 VUS identities and a
946-record temporal cohort: 536 B/LB and 410 P/LP, with 946 gene labels.

No records are invented, manually added, or filter-tuned solely to recover the historical count.
The original historical study and its 1,024-variant documentation remain historical evidence;
they are not rewritten as if they used the 946-record cohort.

### Frozen pipeline and evidence

- t0 archive: `data/raw/clinvar/variant_summary_2025-01.txt.gz`
  - SHA-256: `931322c5b576e4d46c82b2e275ef0920661ef9c39c1acf62ed48e6756f24d7aa`
- t1 archive: `data/raw/clinvar/variant_summary_2026-08.txt.gz`
  - SHA-256: `230ba6d5ac0869bfb46fecb8d19bd8dbfa9a133bfda2e3f8f5b5b662ae7bf500`
- assembly: GRCh38
- variant unit: unique normalized biallelic ACGT germline SNV
- t0 label: exact `Uncertain significance`
- t1 outcome: definitive B/LB or P/LP with the frozen >=2-review-star gate
- t0 release date: 2025-01-02
- t1 release date: 2026-08-06
- authoritative locked-test IDs: `research/ml_extension/splits/authoritative_locked_test_manifest.json`
- generated split manifest: `data/derived/ml_extension/phase3/split_manifest.json`
- deterministic locked-test hash: recorded in the authoritative cohort hash manifest

### Impact and justification

The extension estimand remains a temporal VUS-resolution discrimination study, but its ML-extension
locked-test denominator is now 946 rather than the unavailable historical target of 1,024. The
78-record class-count difference is entirely on the B/LB side; P/LP remains 410. Historical
comparability to reports based on the undocumented 1,024 records is therefore limited and any
comparison must disclose the cohort identity difference. All training/validation/locked-test
overlap, normalized-ID leakage, temporal leakage, gene-group, deterministic-regeneration, and
independent-reference gates must be rechecked against the newly frozen extension cohort before
any downstream model run.

### Approval boundary

This deviation authorizes the ML-extension cohort freeze only. It does not authorize Phase 6
full-cohort inference, Phase 7 embedding extraction, training, HPO, fine-tuning, or locked-test
evaluation. Those remain gated by the master prompt, the final Phase 3/5 checkpoint, and a fresh
current-protocol compute approval.

## ML-DEV-002 — Freeze an immutable GRCh38 reference source for the extension

- Date: 2026-09-21
- Protocol version affected: 1.1.0
- Status: ACCEPTED for the ML-extension study only
- Original-protocol reference statement: `Homo_sapiens_assembly38.fasta`, without an immutable
  source URL, accession/version, byte size, or checksum
- Acquisition script: `research/scripts/acquire_grch38_reference.py`
- Metadata manifest: `data/manifests/grch38.json`
- Implementation commit: `36063e8e1b65ddf1653347a5705e89115e52f1d5` (final frozen-control baseline; initial reference implementation: `dd29318`)

### What changed

The original frozen protocol identified the expected FASTA filename and GRCh38 assembly but did
not freeze an immutable provider object, byte size, SHA-256, FAI checksum, or contig naming
convention. The ML extension therefore freezes the Broad Institute GATK Resource Bundle hg38/v0
object at the canonical uncompressed FASTA URL used by the acquisition script. The provided FAI
object is frozen alongside it. This closes the extension's independent reference-base evidence
gap without modifying the original zero-shot protocol.

### Frozen reference metadata

- Provider: Broad Institute GATK Resource Bundle
- Assembly/build: GRCh38 / `Homo_sapiens_assembly38`
- FASTA URL: `https://storage.googleapis.com/gcp-public-data--broad-references/hg38/v0/Homo_sapiens_assembly38.fasta`
- FAI URL: `https://storage.googleapis.com/gcp-public-data--broad-references/hg38/v0/Homo_sapiens_assembly38.fasta.fai`
- FASTA filename: `Homo_sapiens_assembly38.fasta`
- FAI filename: `Homo_sapiens_assembly38.fasta.fai`
- Expected FASTA size: `3249912778` bytes
- Expected FAI size: `160928` bytes
- Expected FASTA SHA-256: `93157a161863464c9435062fd67c173fdaf99cb8b32f1455018361387ffa5564`
- Expected FAI SHA-256: `edefd93c489dc1baefad312f40388089f8db5cf6dcc3ba0955669ead274e8b6b`
- Contig naming: `chr`-prefixed primary chromosomes (`chr1`-`chr22`, `chrX`, `chrY`), with
  auxiliary HLA/decoy contigs retained under provider-supplied names
- Download date: recorded as `retrieved_at_utc` in `data/manifests/grch38.json`

The large FASTA and FAI remain outside Git under `data/reference/`. Git records only the
acquisition script, source metadata, content hashes, and the independent validation report.
The extension cohort is not promoted until `reference_validation_status = PASS` and unresolved
reference mismatches are zero.
