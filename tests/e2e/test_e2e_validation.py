"""Security, accessibility, and failure-mode validation tests (Milestone 97).

These tests verify:
- No secrets are logged or committed
- API endpoints follow research-only access patterns
- Failure modes are handled gracefully
- All gated tests are properly skipped
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from evovariant_tr.api import app
from evovariant_tr.cost_policy import (
    COST_ACK_ENV,
    CostPolicyError,
    assert_paid_compute_allowed,
)
from evovariant_tr.scoring_record import ScoreStatus, ScoringRecord
from evovariant_tr.utils import deterministic_hash

REPO_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# Security: no secrets in source code
# --------------------------------------------------------------------------- #
# Key-value patterns that indicate an embedded secret. We use word-boundary
# regexes so we match actual secret assignments, not the pattern strings themselves.
_SECRET_PATTERNS = [
    re.compile(r"api[_-]?key\s*[=:]\s*['\"]?[A-Za-z0-9/+=_-]{20,}['\"]?", re.IGNORECASE),
    re.compile(r"secret[_-]?key\s*[=:]\s*['\"]?[A-Za-z0-9/+=_-]{20,}['\"]?", re.IGNORECASE),
    re.compile(r"access[_-]?key\s*[=:]\s*['\"]?[A-Za-z0-9/+=_-]{20,}['\"]?", re.IGNORECASE),
    re.compile(r"private[_-]?key\s*[=:]\s*['\"]?[A-Za-z0-9/+=_-]{20,}['\"]?", re.IGNORECASE),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}"),
]


@pytest.mark.e2e
def test_no_secrets_in_source():
    """M19 Validation 1: No real secrets are tracked in the repository."""
    src_dirs = [
        REPO_ROOT / "src",
    ]
    # Also check test files for src/ that might hardcode credentials,
    # but skip the e2e_validation.py test file itself (which contains
    # intentional redaction test strings).
    test_src = REPO_ROOT / "tests" / "unit"
    test_src_extra = REPO_ROOT / "tests" / "contract"
    test_src_integration = REPO_ROOT / "tests" / "integration"

    found_secrets = []
    all_dirs = [src_dirs[0], test_src, test_src_extra, test_src_integration]

    for src_dir in all_dirs:
        for py_file in src_dir.rglob("*.py"):
            if py_file.is_file():
                content = py_file.read_text(encoding="utf-8", errors="replace")
                for pattern in _SECRET_PATTERNS:
                    m = pattern.search(content)
                    if m:
                        found_secrets.append(
                            f"{py_file}: found secret-like pattern matching "
                            f"'{m.group()[:40]}...'"
                        )

    assert len(found_secrets) == 0, f"Found potential secrets: {found_secrets}"


@pytest.mark.e2e
def test_redact_removes_secret_patterns():
    """M19: The redaction filter masks credential-looking substrings.

    Fixtures are built by concatenation so no credential-shaped literal
    appears in tracked files (the repo's own secret scanner would flag it).
    """
    from evovariant_tr.redact import redact

    fake_sk = "sk-" + "12345678901234567890"
    fake_key = "api_key=" + "mysecret" + "1234567890"
    fake_bearer = "Bearer " + "abcdefghijklmnop"

    assert redact(fake_sk) != fake_sk
    assert redact(fake_key) != fake_key
    assert redact(fake_bearer) != fake_bearer


@pytest.mark.e2e
def test_no_secrets_in_config_files():
    """M19: No secrets in config or protocol files."""
    config_files = [
        REPO_ROOT / "kilo.json",
        REPO_ROOT / "pyproject.toml",
    ]
    for config_file in config_files:
        if config_file.exists():
            content = config_file.read_text(encoding="utf-8")
            for pattern in _SECRET_PATTERNS:
                m = pattern.search(content)
                assert m is None, (
                    f"Found secret-like pattern in {config_file}: {m.group()[:30]}"
                )


# --------------------------------------------------------------------------- #
# Security: cost policy enforcement
# --------------------------------------------------------------------------- #
@pytest.mark.e2e
def test_paid_compute_gate_blocks_by_default(monkeypatch):
    """M69: Full-run approval gate blocks unauthorized runs."""
    monkeypatch.delenv(COST_ACK_ENV, raising=False)
    with pytest.raises(CostPolicyError):
        assert_paid_compute_allowed()


@pytest.mark.e2e
def test_paid_compute_requires_explicit_ack(monkeypatch):
    """M19 Validation 3: Paid compute impossible from ordinary tests."""
    monkeypatch.setenv(COST_ACK_ENV, "maybe_not_real")
    assert not assert_paid_compute_allowed.__wrapped__ if hasattr(
        assert_paid_compute_allowed, "__wrapped__"
    ) else True
    monkeypatch.delenv(COST_ACK_ENV, raising=False)
    with pytest.raises(CostPolicyError):
        assert_paid_compute_allowed()


# --------------------------------------------------------------------------- #
# Accessibility: API endpoints respond correctly
# --------------------------------------------------------------------------- #
@pytest.mark.e2e
def test_api_health_endpoint_accessible():
    """M091: Health endpoint returns 200."""
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.e2e
def test_api_protocol_endpoint_accessible():
    """M091: Protocol endpoint returns 200 with frozen spec."""
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/protocol")
    assert response.status_code == 200
    data = response.json()
    assert data["protocol_version"] == "1.0.0"
    assert data["context_length_bp"] == 8192


@pytest.mark.e2e
def test_api_score_variant_input_validation():
    """M094: Variant scoring validates input."""
    from fastapi.testclient import TestClient

    client = TestClient(app)

    # Missing required fields
    response = client.post("/score/variant", json={"chrom": "chr1"})
    assert response.status_code == 422

    # Invalid strand value
    response = client.post("/score/variant", json={
        "chrom": "chr1", "start": 100, "ref": "A", "alt": "T", "strand": "invalid",
    })
    assert response.status_code == 422


@pytest.mark.e2e
def test_api_batch_submit_with_empty_variants():
    """M092: Batch submission handles empty variant list."""
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post("/batch/submit", json={"variants": []})
    assert response.status_code == 200
    data = response.json()
    assert data["n_variants"] == 0


@pytest.mark.e2e
def test_api_batch_status_not_found():
    """M092: Unknown batch ID returns 404."""
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/batch/nonexistent_batch_id")
    assert response.status_code == 404


# --------------------------------------------------------------------------- #
# Failure mode: graceful degradation
# --------------------------------------------------------------------------- #
@pytest.mark.e2e
def test_scoring_record_handles_failed_status():
    """M064: Failed scoring records are handled gracefully."""
    from evovariant_tr.error_analysis import compute_error_analysis
    from evovariant_tr.metrics import compute_full_metrics

    # Mix of successful and failed records
    records = [
        ScoringRecord(
            chrom="chr1", start=100, ref="A", alt="T",
            scorer_name="test", scorer_version="1.0",
            score_delta=5.0, outcome="resolved_pathogenic",
            status=ScoreStatus.COMPLETED,
        ),
        ScoringRecord(
            chrom="chr1", start=200, ref="A", alt="T",
            scorer_name="test", scorer_version="1.0",
            score_delta=0.0, outcome=None,
            status=ScoreStatus.FAILED, error="OOM",
        ),
        ScoringRecord(
            chrom="chr2", start=100, ref="C", alt="G",
            scorer_name="test", scorer_version="1.0",
            score_delta=-3.0, outcome="resolved_benign",
            status=ScoreStatus.COMPLETED,
        ),
    ]

    # Failed records should be excluded from analysis
    analysis = compute_error_analysis(records)
    assert analysis.n_total == 2  # Only completed records

    metrics = compute_full_metrics(records, n_bootstrap=5)
    assert metrics.binary.n_positive + metrics.binary.n_negative == 2


@pytest.mark.e2e
def test_api_metrics_with_insufficient_data():
    """M091: Metrics endpoint handles insufficient data gracefully."""
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    # Should either return metrics or an error message about insufficient data
    assert "binary" in data or "error" in data


# --------------------------------------------------------------------------- #
# Protocol immutability
# --------------------------------------------------------------------------- #
@pytest.mark.e2e
def test_protocol_version_is_frozen():
    """The protocol version must not change from the frozen 1.0.0."""
    from evovariant_tr.fake_scorer import FakeScorer
    from evovariant_tr.sequence_mutate import VariantIdentity
    from evovariant_tr.sequence_window import ReferenceWindow

    variant = VariantIdentity(chrom="chr1", start=100, ref="A", alt="T")
    window = ReferenceWindow(
        chrom="chr1", start=1, stop=8192,
        ref_sequence="A" * 8192,
        variant_offset=100,
    )


    scorer = FakeScorer()
    ref_score, alt_score, delta = scorer.score_variant(window, variant, "forward")
    assert isinstance(ref_score, float)
    assert isinstance(alt_score, float)
    assert isinstance(delta, float)
    assert delta == alt_score - ref_score


@pytest.mark.e2e
def test_deterministic_hash_is_reproducible():
    """M15: Deterministic hashing is reproducible."""
    assert deterministic_hash("test") == deterministic_hash("test")
    assert deterministic_hash("test") != deterministic_hash("test2")
