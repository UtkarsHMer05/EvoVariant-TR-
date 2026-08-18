# Milestone 015 — Implement deterministic file manifests and hashing

- **MILESTONE:** 015
- **TITLE:** Implement deterministic file manifests and hashing
- **STATUS:** PASS
- **DATE:** 2026-08-18

## WHAT EXISTED BEFORE

- `docs/bootstrap/source_snapshot.sha256` (M2) hashed the legacy snapshot with `shasum`, but there was no reusable manifest machinery in the package.
- The M14 registry's `data_manifests` field expected `{name: sha256}` inputs, but nothing generated them.
- No CLI for verifying assets against a manifest.

## WHAT CHANGED

- Implemented `src/evovariant_tr/manifest.py`:
  - `ManifestEntry` / `Manifest` strict frozen Pydantic models: path, SHA-256, size, compression type, uncompressed checksum, source URL, release date, retrieval time, description.
  - `streaming_sha256` — constant-memory SHA-256 for arbitrarily large archives.
  - `streaming_uncompressed_sha256` — streams gzip through stdlib and records the uncompressed checksum + byte count; zip/zstd recorded as `None` (not practical here, per the "when practical" clause).
  - `sanitize_source_url` — strips userinfo credentials and secret-like query parameters (token, api_key, signature, password, …) so source URLs stay citable but never embed secrets.
  - `release_date` and `retrieved_at` are separate required-to-distinguish fields.
  - `build_manifest` sorts entries by path and rejects duplicates; `manifest_to_json` uses sorted keys → byte-deterministic serialization.
  - `verify_manifest` / `verify_or_raise` re-hash every entry and classify failures as MISSING / SIZE_MISMATCH / HASH_MISMATCH / UNCOMPRESSED_MISMATCH.
- Created `scripts/verify_manifest.py` CLI (exit 0 clean, 1 verification failures, 2 usage error).
- Created `tests/unit/test_manifest.py` (21 tests).

## FILES CREATED

- `src/evovariant_tr/manifest.py`
- `scripts/verify_manifest.py`
- `tests/unit/test_manifest.py`
- `docs/project/reports/milestone_015.md` (this report)

## FILES MODIFIED

- `docs/project/MILESTONE_STATUS.md` (row 015 → PASS)

## FILES REMOVED / MOVED

- None.

## COMMANDS RUN

- `python -m pytest tests/unit/test_manifest.py -q` → **21 passed in 0.41s**
- `python -m pytest tests/unit -q` → **106 passed in 2.37s** (no regressions)
- CLI exercised inside tests via subprocess (exit codes 0/1/2 verified).

## TESTS

- `tests/unit/test_manifest.py` — 21 tests covering:
  - streaming SHA-256 matches hashlib (including chunk_size=3 to exercise the loop);
  - gzip uncompressed checksum/size; zip/zstd return None; suffix-based compression detection;
  - URL sanitization: userinfo removed, secret query params dropped, benign params kept, secret values never leak;
  - entry building records release date and retrieval time separately; missing file raises; bad hash and absolute paths rejected;
  - **Validation 2:** input order does not affect manifest equality or serialized bytes; entries path-sorted; repeated serialization byte-identical; duplicate paths rejected; write/load round-trip;
  - **Validation 1:** one-bit flip on a plain file fails verification (HASH/SIZE_MISMATCH) and `verify_or_raise` raises; one-bit flip on a gzip file detected; missing file reported; forged uncompressed hash reported;
  - CLI exit codes 0 (clean), 1 (corrupted), 2 (missing manifest).

## SCIENTIFIC VALIDATION

- Every future external asset (ClinVar archives, reference genome, comparator files) will be traceable by source, size, retrieval time, and SHA-256 — the provenance chain required before any data milestone (M22+).
- Retrieval time is never conflated with release date, preserving the t0/t1 archive distinction.
- No real data downloaded; tests use synthetic temp files only.

## ENGINEERING VALIDATION

- Determinism proven: same tree + same entries + same timestamp → identical bytes regardless of insertion order.
- Corruption detection proven at one-bit granularity.
- Cloud-free: stdlib + pydantic only. Full unit suite green (106 tests).

## COST / EXTERNAL CALLS

- None. Zero external calls, zero GPU, zero spend.

## EVIDENCE GENERATED

- Test run outputs (21 passed; 106 passed).
- Stage: SYNTHETIC_TEST.

## GIT STATUS

- New files listed above; ledger updated. Local commit to follow; no remote configured, no push.

## RISKS / OPEN QUESTIONS

- Zip/zstd uncompressed checksums are recorded as `None`; if a future comparator ships zstd-compressed, add a streaming decoder then (documented in code).
- `data/manifests/` will receive the first real manifest at M23 (ClinVar t0 download); the registry's `data_manifests` field consumes `{manifest_name: manifest_sha256}`.

## NEXT MILESTONE

- 016 — Create the modern Python project scaffold.

## DO NOT CONTINUE IF

- Any manifest test fails or is skipped.
- One-bit corruption passes verification.
- Manifest serialization is not byte-deterministic.
