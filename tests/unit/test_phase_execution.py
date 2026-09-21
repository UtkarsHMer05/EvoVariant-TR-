"""No-spend tests for the approval-gated Phase 6/7 runner."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from evovariant_tr.cost_policy import load_current_ml_protocol_hash
from evovariant_tr.phase_execution import (
    JsonEndpointClient,
    PhaseExecutionError,
    build_execution_plan,
    execute_cohort,
    load_cohort_records,
    require_current_paid_approval,
)

PROTOCOL_HASH = "a" * 64
MODEL_REVISION = "b" * 40


def _manifest(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "manifest_id": "fixture",
                "records": [
                    {
                        "assembly": "GRCh38",
                        "chromosome": "1",
                        "position_1based": 100,
                        "reference": "A",
                        "alternate": "T",
                        "normalized_variant_id": "GRCh38:1:100:A>T",
                        "split": "TRAIN",
                        "label": 0,
                        "gene_symbol": "GENE1",
                    },
                    {
                        "assembly": "GRCh38",
                        "chromosome": "2",
                        "position_1based": 200,
                        "reference": "C",
                        "alternate": "G",
                        "normalized_variant_id": "GRCh38:2:200:C>G",
                        "split": "VALIDATION",
                        "label": 1,
                        "gene_symbol": "GENE2",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


def _score_endpoint(calls: list[dict[str, object]]):
    def post(request: dict[str, object]) -> dict[str, object]:
        calls.append(request)
        variants = request["variants"]
        assert isinstance(variants, list)
        assert all(isinstance(row, dict) and "label" not in row for row in variants)
        results = []
        for index, variant in enumerate(variants):
            assert isinstance(variant, dict)
            results.append(
                {
                    "status": "completed",
                    "normalized_variant_id": (
                        f"GRCh38:{variant['chromosome']}:{variant['position_1based']}"
                        f":{variant['reference']}>{variant['alternate']}"
                    ),
                    "score_delta": float(index + 1),
                    "provenance": {"scoring_semantics": "alternate_minus_reference"},
                }
            )
        return {"status": "completed", "results": results}

    return post


def _plan(records, manifest_hash, *, endpoint_kind="score", labels=False):
    return build_execution_plan(
        records,
        phase=6 if endpoint_kind == "score" else 7,
        family="ZS" if endpoint_kind == "score" else "REP",
        endpoint_kind=endpoint_kind,
        model_id="evo2",
        checkpoint="evo2_7b",
        model_revision=MODEL_REVISION,
        protocol_hash=PROTOCOL_HASH,
        cohort_manifest_sha256=manifest_hash,
        split_manifest_sha256=None,
        shard_size=1,
        batch_size=1,
        include_labels_in_output=labels,
        embedding_layer=("blocks.28.mlp.l3" if endpoint_kind == "embedding" else None),
    )


def test_manifest_loader_reconciles_source_and_chr_identity(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _manifest(manifest)

    records, digest = load_cohort_records(manifest, splits={"TRAIN", "VALIDATION"})

    assert len(records) == 2
    assert records[0].source_normalized_variant_id == "GRCh38:1:100:A>T"
    assert records[0].canonical_normalized_variant_id == "GRCh38:chr1:100:A>T"
    assert len(digest) == 64
    assert records[0].request_payload() == {
        "assembly": "GRCh38",
        "chromosome": "chr1",
        "position_1based": 100,
        "reference": "A",
        "alternate": "T",
    }


def test_score_execution_is_resumable_and_label_free_at_transport(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _manifest(manifest)
    records, manifest_hash = load_cohort_records(manifest)
    plan = _plan(records, manifest_hash)
    calls: list[dict[str, object]] = []

    summary = execute_cohort(
        records,
        plan=plan,
        output_dir=tmp_path / "run",
        endpoint=_score_endpoint(calls),
    )

    assert summary["status"] == "COMPLETED"
    assert summary["record_count"] == 2
    assert len(calls) == 2
    output = (tmp_path / "run" / "predictions.jsonl").read_text(encoding="utf-8")
    rows = [json.loads(line) for line in output.splitlines()]
    assert [row["normalized_variant_id"] for row in rows] == [
        "GRCh38:1:100:A>T",
        "GRCh38:2:200:C>G",
    ]
    assert all("label" not in row for row in rows)

    def should_not_run(_: dict[str, object]) -> dict[str, object]:
        raise AssertionError("completed shards must be skipped on resume")

    resumed = execute_cohort(
        records,
        plan=plan,
        output_dir=tmp_path / "run",
        endpoint=should_not_run,
    )
    assert resumed["completed_shards"] == 2


def test_tampered_shard_fails_closed(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _manifest(manifest)
    records, manifest_hash = load_cohort_records(manifest)
    plan = _plan(records, manifest_hash)
    execute_cohort(
        records,
        plan=plan,
        output_dir=tmp_path / "run",
        endpoint=_score_endpoint([]),
    )
    shard = next((tmp_path / "run" / "shards").glob("*.json"))
    document = json.loads(shard.read_text(encoding="utf-8"))
    document["rows"][0]["raw_score"] = 999.0
    shard.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(PhaseExecutionError, match="tampered shard"):
        execute_cohort(
            records,
            plan=plan,
            output_dir=tmp_path / "run",
            endpoint=_score_endpoint([]),
        )


def _embedding_payload(normalized_variant_id: str) -> dict[str, object]:
    def values(seed: float) -> dict[str, object]:
        reference = [seed, seed + 1.0]
        alternate = [seed + 1.0, seed + 3.0]
        difference = [alt - ref for ref, alt in zip(reference, alternate, strict=True)]

        def digest(vector: list[float]) -> str:
            encoded = json.dumps(vector, separators=(",", ":")).encode("utf-8")
            return hashlib.sha256(encoded).hexdigest()

        return {
            "reference": reference,
            "alternate": alternate,
            "difference": difference,
            "shape": [2],
            "dtype": "float32",
            "reference_sha256": digest(reference),
            "alternate_sha256": digest(alternate),
            "difference_sha256": digest(difference),
        }

    return {
        "status": "completed",
        "normalized_variant_id": normalized_variant_id,
        "embedding_features": {"forward": values(1.0), "reverse": values(3.0)},
        "provenance": {
            "layer": "blocks.28.mlp.l3",
            "pooling": "mean_tokens",
        },
    }


def test_embedding_execution_writes_hashed_features_without_labels(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _manifest(manifest)
    records, manifest_hash = load_cohort_records(manifest, splits={"VALIDATION"})
    plan = _plan(records, manifest_hash, endpoint_kind="embedding")
    calls: list[dict[str, object]] = []

    def endpoint(request: dict[str, object]) -> dict[str, object]:
        calls.append(request)
        variant = request["variants"][0]
        assert isinstance(variant, dict)
        return {
            "status": "completed",
            "results": [
                _embedding_payload(
                    f"GRCh38:{variant['chromosome']}:{variant['position_1based']}"
                    f":{variant['reference']}>{variant['alternate']}"
                )
            ],
        }

    summary = execute_cohort(
        records,
        plan=plan,
        output_dir=tmp_path / "features",
        endpoint=endpoint,
        embedding_layer="blocks.28.mlp.l3",
    )

    assert summary["endpoint_kind"] == "embedding"
    assert calls[0]["layer"] == "blocks.28.mlp.l3"
    row = json.loads(
        (tmp_path / "features" / "features.jsonl").read_text(encoding="utf-8")
    )
    assert row["normalized_variant_id"] == "GRCh38:2:200:C>G"
    assert row["model_normalized_variant_id"] == "GRCh38:chr2:200:C>G"
    assert row["gene_symbol"] == "GENE2"
    assert "label" not in row

    labeled_plan = _plan(
        records,
        manifest_hash,
        endpoint_kind="embedding",
        labels=True,
    )
    execute_cohort(
        records,
        plan=labeled_plan,
        output_dir=tmp_path / "labeled-features",
        endpoint=endpoint,
        embedding_layer="blocks.28.mlp.l3",
    )
    labeled_row = json.loads(
        (tmp_path / "labeled-features" / "features.jsonl").read_text(encoding="utf-8")
    )
    assert labeled_row["label"] == 1


def test_manifest_id_mismatch_fails_before_execution(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _manifest(manifest)
    document = json.loads(manifest.read_text(encoding="utf-8"))
    document["records"][0]["normalized_variant_id"] = "GRCh38:1:101:A>T"
    manifest.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(PhaseExecutionError, match="does not match"):
        load_cohort_records(manifest)


def test_paid_gate_rejects_stale_approval_before_remote_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EVOVARIANT_TR_PAID_COMPUTE_ACK", "I_ACCEPT_COSTS")

    with pytest.raises(PhaseExecutionError, match="protocol_hash"):
        require_current_paid_approval(
            Path("artifacts/approvals/full_run_approval.json"),
            scope_tokens=("full Phase 6",),
        )


def test_paid_gate_requires_acknowledgement(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EVOVARIANT_TR_PAID_COMPUTE_ACK", raising=False)

    with pytest.raises(PhaseExecutionError, match="paid compute is blocked"):
        require_current_paid_approval(
            Path("artifacts/approvals/full_run_approval.json"),
            scope_tokens=("full Phase 6",),
        )


def test_json_endpoint_client_validation_and_transport_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="explicit http"):
        JsonEndpointClient("modal://not-http")
    with pytest.raises(ValueError, match="timeout"):
        JsonEndpointClient("https://example.test", timeout_seconds=0)

    class Response:
        def __init__(self, body: bytes) -> None:
            self.body = body

        def __enter__(self) -> Response:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return self.body

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout: Response(b'{"status":"completed"}'),
    )
    assert JsonEndpointClient("https://example.test")({"variants": []}) == {
        "status": "completed"
    }

    def network_failure(request: object, timeout: float) -> Response:
        raise OSError("network down")

    monkeypatch.setattr("urllib.request.urlopen", network_failure)
    with pytest.raises(PhaseExecutionError, match="request failed"):
        JsonEndpointClient("https://example.test")({})

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout: Response(b"[]"),
    )
    with pytest.raises(PhaseExecutionError, match="response must be an object"):
        JsonEndpointClient("https://example.test")({})


def test_current_paid_gate_accepts_matching_scope_and_rejects_missing_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    approval = tmp_path / "approval.json"
    approval.write_text(
        json.dumps(
            {
                "approved_by": "test",
                "approved_at": "2026-09-21",
                "max_budget_usd": 2.0,
                "run_scope": "full Phase 6 Evo2 benchmark",
                "modal_environment": "evovariant-tr",
                "gpu_type": "H100",
                "protocol_hash": load_current_ml_protocol_hash(),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("EVOVARIANT_TR_PAID_COMPUTE_ACK", "I_ACCEPT_COSTS")
    accepted = require_current_paid_approval(
        approval,
        scope_tokens=("full Phase 6", "Evo2"),
    )
    assert accepted.max_budget_usd == 2.0
    with pytest.raises(PhaseExecutionError, match="scope"):
        require_current_paid_approval(approval, scope_tokens=("Phase 7",))


def test_loader_rejects_invalid_documents_and_labels(tmp_path: Path) -> None:
    missing_records = tmp_path / "missing.json"
    missing_records.write_text("{}", encoding="utf-8")
    with pytest.raises(PhaseExecutionError, match="records list"):
        load_cohort_records(missing_records)

    non_object = tmp_path / "non-object.json"
    non_object.write_text(json.dumps({"records": ["bad"]}), encoding="utf-8")
    with pytest.raises(PhaseExecutionError, match="JSON objects"):
        load_cohort_records(non_object)

    empty_selection = tmp_path / "empty-selection.json"
    _manifest(empty_selection)
    with pytest.raises(PhaseExecutionError, match="empty"):
        load_cohort_records(empty_selection, splits={"LOCKED_TEST"})

    invalid_label = tmp_path / "invalid-label.json"
    _manifest(invalid_label)
    document = json.loads(invalid_label.read_text(encoding="utf-8"))
    document["records"][0]["label"] = 3
    invalid_label.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(PhaseExecutionError, match="binary"):
        load_cohort_records(invalid_label)

    no_label = tmp_path / "no-label.json"
    _manifest(no_label)
    document = json.loads(no_label.read_text(encoding="utf-8"))
    document["records"][0].pop("label")
    no_label.write_text(json.dumps(document), encoding="utf-8")
    records, _ = load_cohort_records(no_label, splits={"TRAIN"})
    assert records[0].label is None

    unsupported_split = tmp_path / "unsupported-split.json"
    _manifest(unsupported_split)
    document = json.loads(unsupported_split.read_text(encoding="utf-8"))
    document["records"][0]["split"] = "OTHER"
    unsupported_split.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(PhaseExecutionError, match="unsupported"):
        load_cohort_records(unsupported_split)


def test_loader_rejects_duplicates_and_unreadable_manifest(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    _manifest(duplicate)
    document = json.loads(duplicate.read_text(encoding="utf-8"))
    document["records"].append(dict(document["records"][0]))
    duplicate.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(PhaseExecutionError, match="duplicate source"):
        load_cohort_records(duplicate)

    with pytest.raises(PhaseExecutionError, match="could not read"):
        load_cohort_records(tmp_path / "does-not-exist.json")


def test_execution_plan_rejects_invalid_freeze_inputs(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _manifest(manifest)
    records, digest = load_cohort_records(manifest)
    common = {
        "records": records,
        "family": "ZS",
        "endpoint_kind": "score",
        "model_id": "evo2",
        "checkpoint": "evo2_7b",
        "model_revision": MODEL_REVISION,
        "protocol_hash": PROTOCOL_HASH,
        "cohort_manifest_sha256": digest,
        "split_manifest_sha256": None,
    }
    with pytest.raises(ValueError, match="Phase 6"):
        build_execution_plan(phase=5, **common)
    with pytest.raises(ValueError, match="non-empty"):
        build_execution_plan(
            phase=6,
            family="",
            **{key: value for key, value in common.items() if key != "family"},
        )
    with pytest.raises(ValueError, match="SHA-256"):
        build_execution_plan(phase=6, **{**common, "protocol_hash": "bad"})
    with pytest.raises(ValueError, match="positive"):
        build_execution_plan(phase=6, shard_size=0, **common)
    with pytest.raises(ValueError, match="at least one"):
        build_execution_plan(phase=6, **{**common, "records": []})
    with pytest.raises(ValueError, match="required"):
        build_execution_plan(
            phase=7,
            endpoint_kind="embedding",
            **{key: value for key, value in common.items() if key != "endpoint_kind"},
        )
    with pytest.raises(ValueError, match="only valid"):
        build_execution_plan(phase=6, embedding_layer="layer", **common)


def test_score_execution_supports_fallback_identity_and_explicit_labels(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "manifest.json"
    _manifest(manifest)
    records, digest = load_cohort_records(manifest, splits={"TRAIN"})
    plan = build_execution_plan(
        records,
        phase=6,
        family="ZS",
        endpoint_kind="score",
        model_id="evo2",
        checkpoint="evo2_7b",
        model_revision=MODEL_REVISION,
        protocol_hash=PROTOCOL_HASH,
        cohort_manifest_sha256=digest,
        split_manifest_sha256=None,
        include_labels_in_output=True,
    )

    def endpoint(request: dict[str, object]) -> dict[str, object]:
        variant = request["variants"][0]
        assert isinstance(variant, dict)
        return {
            "status": "completed",
            "results": [
                {
                    "status": "completed",
                    "assembly": "GRCh38",
                    "chromosome": variant["chromosome"],
                    "position_1based": variant["position_1based"],
                    "reference": variant["reference"],
                    "alternate": variant["alternate"],
                    "delta_primary": 0.25,
                }
            ],
        }

    execute_cohort(
        records,
        plan=plan,
        output_dir=tmp_path / "labeled",
        endpoint=endpoint,
    )
    row = json.loads(
        (tmp_path / "labeled" / "predictions.jsonl").read_text(encoding="utf-8")
    )
    assert row["label"] == 0
    assert row["raw_score"] == 0.25


def test_execution_response_validation_fails_closed(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _manifest(manifest)
    records, digest = load_cohort_records(manifest, splits={"TRAIN"})
    plan = _plan(records, digest)
    record = records[0]
    identity = record.canonical_normalized_variant_id

    def run(response: object, name: str) -> None:
        def endpoint(_: dict[str, object]) -> object:
            return response

        with pytest.raises(PhaseExecutionError):
            execute_cohort(
                records,
                plan=plan,
                output_dir=tmp_path / name,
                endpoint=endpoint,  # type: ignore[arg-type]
            )

    run([], "not-object")
    run({"status": "failed"}, "failed-status")
    run({"status": "completed", "results": []}, "wrong-count")
    run({"status": "completed", "results": ["bad"]}, "non-object-row")
    run(
        {
            "status": "completed",
            "results": [{"status": "failed", "normalized_variant_id": identity}],
        },
        "failed-row",
    )
    run(
        {
            "status": "completed",
            "results": [
                {
                    "status": "completed",
                    "normalized_variant_id": identity,
                    "score_delta": float("nan"),
                }
            ],
        },
        "nonfinite-score",
    )
    run(
        {
            "status": "completed",
            "results": [
                {
                    "status": "completed",
                    "normalized_variant_id": "GRCh38:chr1:999:A>T",
                    "score_delta": 1.0,
                }
            ],
        },
        "mismatched-id",
    )

    def duplicate_endpoint(_: dict[str, object]) -> dict[str, object]:
        return {
            "status": "completed",
            "results": [
                {
                    "status": "completed",
                    "normalized_variant_id": identity,
                    "score_delta": 1.0,
                },
                {
                    "status": "completed",
                    "normalized_variant_id": identity,
                    "score_delta": 2.0,
                },
            ],
        }

    two_records, two_digest = load_cohort_records(manifest)
    two_plan = build_execution_plan(
        two_records,
        phase=6,
        family="ZS",
        endpoint_kind="score",
        model_id="evo2",
        checkpoint="evo2_7b",
        model_revision=MODEL_REVISION,
        protocol_hash=PROTOCOL_HASH,
        cohort_manifest_sha256=two_digest,
        split_manifest_sha256=None,
        shard_size=2,
        batch_size=2,
    )
    with pytest.raises(PhaseExecutionError, match="duplicate"):
        execute_cohort(
            two_records,
            plan=two_plan,
            output_dir=tmp_path / "duplicate-response",
            endpoint=duplicate_endpoint,
        )


def test_embedding_layer_and_identity_guards(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _manifest(manifest)
    records, digest = load_cohort_records(manifest, splits={"VALIDATION"})
    plan = _plan(records, digest, endpoint_kind="embedding")
    with pytest.raises(PhaseExecutionError, match="embedding layer"):
        execute_cohort(
            records,
            plan=plan,
            output_dir=tmp_path / "wrong-layer",
            endpoint=lambda _: {"status": "completed", "results": []},
            embedding_layer="wrong.layer",
        )

    def bad_embedding(_: dict[str, object]) -> dict[str, object]:
        return {
            "status": "completed",
            "results": [
                _embedding_payload("GRCh38:chr9:900:A>T"),
            ],
        }

    with pytest.raises(PhaseExecutionError, match="duplicate or unknown"):
        execute_cohort(
            records,
            plan=plan,
            output_dir=tmp_path / "wrong-embedding-id",
            endpoint=bad_embedding,
            embedding_layer="blocks.28.mlp.l3",
        )

    def wrong_layer(_: dict[str, object]) -> dict[str, object]:
        payload = _embedding_payload("GRCh38:chr2:200:C>G")
        assert isinstance(payload["provenance"], dict)
        payload["provenance"]["layer"] = "blocks.27.mlp.l3"
        return {"status": "completed", "results": [payload]}

    with pytest.raises(PhaseExecutionError, match="unexpected embedding layer"):
        execute_cohort(
            records,
            plan=plan,
            output_dir=tmp_path / "wrong-embedding-layer",
            endpoint=wrong_layer,
            embedding_layer="blocks.28.mlp.l3",
        )


def test_execution_rejects_frozen_input_mismatches(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    _manifest(manifest)
    records, digest = load_cohort_records(manifest)
    plan = _plan(records, digest)
    endpoint = _score_endpoint([])
    with pytest.raises(PhaseExecutionError, match="match the frozen"):
        execute_cohort(records[:1], plan=plan, output_dir=tmp_path / "short", endpoint=endpoint)
    with pytest.raises(PhaseExecutionError, match="sorted"):
        execute_cohort(
            list(reversed(records)),
            plan=plan,
            output_dir=tmp_path / "reverse",
            endpoint=endpoint,
        )
    with pytest.raises(PhaseExecutionError, match="label output"):
        execute_cohort(
            records,
            plan=plan,
            output_dir=tmp_path / "labels",
            endpoint=endpoint,
            include_labels_in_output=True,
        )

    execute_cohort(records, plan=plan, output_dir=tmp_path / "plan", endpoint=endpoint)
    changed = _plan(records, digest)
    changed = build_execution_plan(
        records,
        phase=6,
        family="DIFFERENT",
        endpoint_kind="score",
        model_id="evo2",
        checkpoint="evo2_7b",
        model_revision=MODEL_REVISION,
        protocol_hash=PROTOCOL_HASH,
        cohort_manifest_sha256=digest,
        split_manifest_sha256=None,
    )
    with pytest.raises(PhaseExecutionError, match="existing execution plan"):
        execute_cohort(records, plan=changed, output_dir=tmp_path / "plan", endpoint=endpoint)
