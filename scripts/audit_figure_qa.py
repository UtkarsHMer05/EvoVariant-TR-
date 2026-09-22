#!/usr/bin/env python3
"""Audit the rendered publication families and build a no-dependency gallery."""

# ruff: noqa: E501

from __future__ import annotations

import base64
import hashlib
import html
import json
import math
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "research/reports/phase17/FIGURE_INVENTORY.json"
MANIFEST = ROOT / "research/reports/phase17/publication_manifest.json"
OUT = ROOT / "artifacts/audits"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def command_output(command: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return result.returncode, result.stdout, result.stderr


def parse_pdf_info(path: Path) -> dict[str, str]:
    executable = shutil.which("pdfinfo")
    if executable is None:
        return {"status": "NOT_AVAILABLE"}
    code, stdout, stderr = command_output([executable, str(path)])
    values: dict[str, str] = {"status": "PASS" if code == 0 else "FAIL"}
    for line in stdout.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            if key in {"Pages", "Page size"}:
                values[key] = value.strip()
    if code != 0:
        values["stderr"] = stderr.strip()[:300]
    return values


def png_info(path: Path) -> dict[str, str]:
    executable = shutil.which("sips")
    if executable is None:
        return {"status": "NOT_AVAILABLE"}
    code, stdout, stderr = command_output([executable, "-g", "pixelWidth", "-g", "pixelHeight", str(path)])
    values: dict[str, str] = {"status": "PASS" if code == 0 else "FAIL"}
    for line in stdout.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            if key in {"pixelWidth", "pixelHeight"}:
                values[key] = value.strip()
    if code != 0:
        values["stderr"] = stderr.strip()[:300]
    return values


def svg_bounds(root: ET.Element) -> list[str]:
    issues: list[str] = []
    view_box = root.attrib.get("viewBox", "").split()
    if len(view_box) != 4 or not all(finite(value) for value in view_box):
        return ["invalid viewBox"]
    _, _, width, height = map(float, view_box)
    if width <= 0 or height <= 0:
        return ["non-positive viewBox"]
    for element in root.iter():
        for attribute in ("x", "y", "x1", "y1", "x2", "y2", "cx", "cy"):
            if attribute not in element.attrib or not finite(element.attrib[attribute]):
                continue
            value = float(element.attrib[attribute])
            if value < -5 or value > (width + 5 if attribute.startswith("x") or attribute == "cx" else height + 5):
                issues.append(f"{attribute}={value:g} outside viewBox")
        if element.tag.endswith("rect"):
            x = float(element.attrib.get("x", 0))
            y = float(element.attrib.get("y", 0))
            w = float(element.attrib.get("width", 0))
            h = float(element.attrib.get("height", 0))
            if x + w > width + 5 or y + h > height + 5 or x < -5 or y < -5:
                issues.append("rect outside viewBox")
    return sorted(set(issues))


def trend_check(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[float]] = {}
    nonfinite = 0
    for row in rows:
        for key in ("x_numeric", "y", "value"):
            if key in row and row[key] is not None and (key != "y" or isinstance(row[key], (int, float))) and not finite(row[key]):
                nonfinite += 1
        if "x_numeric" in row and row.get("x_numeric") is not None:
            groups.setdefault(str(row.get("series", "__single__")), []).append(float(row["x_numeric"]))
    directions: dict[str, str] = {}
    nonmonotonic: list[str] = []
    for series, values in groups.items():
        rising = all(b >= a for a, b in zip(values, values[1:], strict=False))
        falling = all(b <= a for a, b in zip(values, values[1:], strict=False))
        if not (rising or falling):
            nonmonotonic.append(series)
        else:
            directions[series] = "ascending" if rising else "descending"
    return {"status": "PASS" if nonfinite == 0 and not nonmonotonic else "FAIL", "nonfinite_values": nonfinite, "nonmonotonic_series": nonmonotonic, "series_directions": directions}


def main() -> int:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ready = [entry for entry in inventory["figures"] if entry.get("status") == "READY"]
    results: list[dict[str, Any]] = []
    png_payloads: list[tuple[str, bytes]] = []
    with tempfile.TemporaryDirectory(prefix="figure-qa-") as temporary:
        temp_root = Path(temporary)
        pdftoppm = shutil.which("pdftoppm")
        for entry in ready:
            figure_id = entry["figure_id"]
            issues: list[str] = []
            svg_path = ROOT / next(path for path in entry["output_paths"] if path.endswith(".svg"))
            png_path = ROOT / next(path for path in entry["output_paths"] if path.endswith(".png"))
            pdf_path = ROOT / next(path for path in entry["output_paths"] if path.endswith(".pdf"))
            for path in (svg_path, png_path, pdf_path):
                if not path.is_file():
                    issues.append(f"missing output: {path.relative_to(ROOT)}")
            for relative, expected in manifest.get("output_hashes", {}).items():
                if relative in entry["output_paths"] and (not (ROOT / relative).is_file() or sha(ROOT / relative) != expected):
                    issues.append(f"manifest hash mismatch: {relative}")
            source = ROOT / entry["derived_source"]
            if not source.is_file():
                issues.append("missing derived source sidecar")
                rows = []
            else:
                source_payload = json.loads(source.read_text(encoding="utf-8"))
                rows = source_payload.get("rows", [])
                for artifact in entry.get("source_artifacts", []):
                    target = ROOT / artifact["path"]
                    if not target.is_file() or sha(target) != artifact["sha256"]:
                        issues.append(f"source hash mismatch: {artifact['path']}")
            if svg_path.is_file():
                raw_svg = svg_path.read_text(encoding="utf-8")
                if any(token in raw_svg for token in ("NaN", "nan", "undefined")):
                    issues.append("non-finite or undefined SVG token")
                try:
                    root = ET.fromstring(raw_svg)
                    issues.extend(svg_bounds(root))
                    visible_text = " ".join(root.itertext())
                    for required in (entry["figure_id"], entry["evidence_stage"], entry["population"], entry["caption"], *entry["axes"]):
                        if str(required) not in visible_text:
                            issues.append(f"missing visible label: {required}")
                    if f"n={entry['n']}" not in visible_text:
                        issues.append("missing sample-size marker")
                except ET.ParseError as exc:
                    issues.append(f"SVG parse failure: {exc}")
            pdf_info = parse_pdf_info(pdf_path) if pdf_path.is_file() else {"status": "MISSING"}
            if pdf_info.get("status") == "FAIL":
                issues.append("PDF metadata/render check failed")
            if pdf_info.get("Pages") not in {None, "1"}:
                issues.append(f"PDF page count is {pdf_info['Pages']}")
            image_info = png_info(png_path) if png_path.is_file() else {"status": "MISSING"}
            if image_info.get("status") == "FAIL":
                issues.append("PNG dimension check failed")
            if pdftoppm and pdf_path.is_file():
                render_prefix = temp_root / figure_id
                code, _, stderr = command_output([pdftoppm, "-f", "1", "-l", "1", "-png", "-singlefile", str(pdf_path), str(render_prefix)])
                if code != 0:
                    issues.append(f"PDF rasterization failed: {stderr.strip()[:200]}")
            trend = trend_check(rows)
            if trend["status"] == "FAIL":
                issues.append("source trend/numeric validity failed")
            if png_path.is_file():
                png_payloads.append((figure_id, png_path.read_bytes()))
            results.append({
                "figure_id": figure_id,
                "status": "PASS" if not issues else "FAIL",
                "issues": sorted(set(issues)),
                "evidence_stage": entry["evidence_stage"],
                "population": entry["population"],
                "n": entry["n"],
                "axes": entry["axes"],
                "caption": entry["caption"],
                "trend_validity": trend,
                "source_sha256": {artifact["path"]: artifact["sha256"] for artifact in entry.get("source_artifacts", [])},
                "output_paths": entry["output_paths"],
                "pdf": pdf_info,
                "png": image_info,
            })

    columns = 5
    cell_w, cell_h = 260, 185
    rows_count = (len(png_payloads) + columns - 1) // columns
    sheet_w, sheet_h = columns * cell_w, rows_count * cell_h
    images: list[str] = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{sheet_w}" height="{sheet_h}" viewBox="0 0 {sheet_w} {sheet_h}">', '<rect width="100%" height="100%" fill="#f8fafc"/>']
    for index, (figure_id, payload) in enumerate(png_payloads):
        x = (index % columns) * cell_w
        y = (index // columns) * cell_h
        encoded = base64.b64encode(payload).decode("ascii")
        images.append(f'<rect x="{x + 4}" y="{y + 4}" width="{cell_w - 8}" height="{cell_h - 8}" rx="5" fill="#ffffff" stroke="#cbd5e1"/>')
        images.append(f'<image x="{x + 12}" y="{y + 8}" width="{cell_w - 24}" height="{cell_h - 34}" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{encoded}"/>')
        images.append(f'<text x="{x + 10}" y="{y + cell_h - 10}" font-family="Arial" font-size="11" fill="#172033">{html.escape(figure_id)}</text>')
    images.append("</svg>")
    contact_svg = OUT / "figure_qa_contact_sheet.svg"
    contact_png = OUT / "figure_qa_contact_sheet.png"
    contact_svg.write_text("".join(images), encoding="utf-8")
    converter = shutil.which("rsvg-convert")
    if converter:
        command_output([converter, "--format=png", "-o", str(contact_png), str(contact_svg)])

    cards = []
    for result in results:
        relative_png = next(path for path in result["output_paths"] if path.endswith(".png"))
        cards.append(f'<article><h2>{html.escape(result["figure_id"])}</h2><img src="../../{html.escape(relative_png)}" alt="{html.escape(result["figure_id"])}"><p><b>{result["status"]}</b> · {html.escape(result["evidence_stage"])} · n={result["n"]}<br>{html.escape(result["population"])}<br>{html.escape("; ".join(result["axes"]))}</p><p>{html.escape(result["caption"])}</p><p><a href="../../{html.escape(next(path for path in result["output_paths"] if path.endswith(".svg")))}">SVG</a> · <a href="../../{html.escape(next(path for path in result["output_paths"] if path.endswith(".pdf")))}">PDF</a></p></article>')
    gallery = "<!doctype html><meta charset='utf-8'><title>EvoVariant-TR figure QA gallery</title><style>body{font-family:Arial,sans-serif;background:#f8fafc;color:#172033}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}article{background:white;border:1px solid #cbd5e1;border-radius:8px;padding:10px}img{max-width:100%;height:180px;object-fit:contain;display:block;margin:auto}h2{font-size:16px;margin:4px 0}p{font-size:12px;line-height:1.35}</style><h1>EvoVariant-TR figure QA gallery</h1><p>39 rendered families; see <code>FIGURE_QA.md</code> for automated checks and source hashes.</p><main>" + "".join(cards) + "</main>"
    (OUT / "figure_qa_gallery.html").write_text(gallery, encoding="utf-8")

    failed = [result for result in results if result["status"] != "PASS"]
    payload = {
        "schema_version": "figure-qa-v1",
        "status": "PASS_AUTOMATED_STRUCTURAL_QA" if not failed else "FAIL",
        "recorded_at_utc": datetime.now(UTC).isoformat(),
        "inventory": str(INVENTORY.relative_to(ROOT)),
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "rendered_family_count": len(results),
        "expected_rendered_family_count": 39,
        "manual_visual_review": "PENDING_CONTACT_SHEET_REVIEW",
        "contact_sheet": str(contact_png.relative_to(ROOT)) if contact_png.is_file() else str(contact_svg.relative_to(ROOT)),
        "gallery": str((OUT / "figure_qa_gallery.html").relative_to(ROOT)),
        "results": results,
    }
    (OUT / "figure_qa_manifest.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Figure QA — EvoVariant-TR Phase 17",
        "",
        f"Automated status: `{payload['status']}` across **{len(results)} rendered families** (expected 39).",
        "Manual visual contact-sheet review: `PENDING_CONTACT_SHEET_REVIEW`.",
        "",
        "Outputs: [contact sheet](figure_qa_contact_sheet.png), [SVG contact sheet](figure_qa_contact_sheet.svg), and [HTML gallery](figure_qa_gallery.html).",
        "",
        "The audit checks output existence and publication-manifest hashes, SVG XML/viewBox validity, finite coordinates, visible titles/evidence stages/populations/sample-size markers/axis labels/captions, PNG dimensions, one-page PDF metadata, PDF rasterization, finite source values, and monotonic x-order within each plotted series. Ascending and descending source order are both accepted; no trend is inferred beyond the recorded rows.",
        "",
        "| Figure | Status | Stage | n | Axes | Trend validity | Issues |",
        "|---|---|---|---:|---|---|---|",
    ]
    for result in results:
        trend = result["trend_validity"]["status"]
        issues = "; ".join(result["issues"]) or "none"
        lines.append(f"| {result['figure_id']} | {result['status']} | {result['evidence_stage']} | {result['n']} | {' / '.join(result['axes'])} | {trend} | {issues} |")
    lines.extend([
        "",
        "Source hashes are preserved per figure in `figure_qa_manifest.json` and in the existing source sidecars. The two inventory entries marked `NOT_APPLICABLE_WITH_DOCUMENTED_REASON` are intentionally excluded from the rendered-family count and are not treated as missing figures.",
        "",
    ])
    (OUT / "FIGURE_QA.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "rendered_families": len(results), "failed": len(failed), "contact_sheet": payload["contact_sheet"]}, indent=2))
    return 0 if not failed and len(results) == 39 else 1


if __name__ == "__main__":
    raise SystemExit(main())
