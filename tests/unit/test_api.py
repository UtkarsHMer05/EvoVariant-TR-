"""Tests for api.py — Milestones 91-92."""

from __future__ import annotations

from fastapi.testclient import TestClient

from evovariant_tr.api import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["scorer"] == "fake_scorer"


def test_protocol_endpoint():
    response = client.get("/protocol")
    assert response.status_code == 200
    data = response.json()
    assert data["context_length_bp"] == 8192
    assert data["protocol_version"] == "1.0.0"


def test_score_single_variant():
    response = client.post("/score/variant", json={
        "chrom": "chr1",
        "start": 100,
        "ref": "A",
        "alt": "T",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["variant"] == "chr1:g.100A>T"
    assert "reference_score" in data
    assert "alternate_score" in data
    assert "score_delta" in data
    assert "provenance" in data
    assert isinstance(data["score_delta"], float)


def test_score_single_variant_reverse_strand():
    response = client.post("/score/variant", json={
        "chrom": "chr1",
        "start": 100,
        "ref": "A",
        "alt": "T",
        "strand": "reverse",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"


def test_score_batch_variants():
    response = client.post("/score/batch", json={
        "variants": [
            {"chrom": "chr1", "start": 100, "ref": "A", "alt": "T"},
            {"chrom": "chr1", "start": 200, "ref": "C", "alt": "G"},
        ],
        "description": "test batch",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["scored"] == 2
    assert len(data["results"]) == 2
    assert data["failures"] == []


def test_submit_batch_job():
    response = client.post("/batch/submit", json={
        "variants": [
            {"chrom": "chr1", "start": 100, "ref": "A", "alt": "T"},
        ],
        "description": "test job",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert "job_id" in data
    assert data["n_variants"] == 1
    assert "/batch/" in data["check_url"]


def test_get_batch_status():
    # First submit a job
    submit_resp = client.post("/batch/submit", json={
        "variants": [
            {"chrom": "chr1", "start": 100, "ref": "A", "alt": "T"},
        ],
    })
    job_id = submit_resp.json()["job_id"]

    # Then check status
    status_resp = client.get(f"/batch/{job_id}")
    assert status_resp.status_code == 200
    data = status_resp.json()
    assert data["status"] == "queued"
    assert data["n_variants"] == 1


def test_get_batch_status_not_found():
    response = client.get("/batch/nonexistent_job_id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_result_not_found():
    response = client.get("/results/nonexistent")
    assert response.status_code == 404


def test_metrics_empty_registry():
    # The registry might be empty in a fresh test
    # so /metrics should return either metrics or an error message
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    # Could be either metrics or "not enough records"
    assert "binary" in data or "error" in data


def test_metrics_with_data():
    # Submit a score first
    client.post("/score/variant", json={
        "chrom": "chr1", "start": 100, "ref": "A", "alt": "T",
    })
    response = client.get("/metrics")
    assert response.status_code == 200
    # May or may not have enough records for metrics
    data = response.json()
    assert "binary" in data or "error" in data