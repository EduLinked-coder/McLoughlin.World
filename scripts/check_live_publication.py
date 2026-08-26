#!/usr/bin/env python3
"""Read-only checks against the live McLoughlin.world publication surface.

This script detects drift between repository expectations and the public site.
It never changes canonical content and should be treated as a monitoring aid,
not as publication authority.

The SSA release-integrity check reuses the canonical release manifest. It
records hosted SHA-256 hashes, compares exact repository-side copies where they
actually exist, and compares separately hosted artefacts with matching members
inside the published ZIP. Missing exact repository copies remain explicit and
must never be promoted to byte-identity claims.
"""

from __future__ import annotations

import hashlib
import io
import json
import sys
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "McLoughlin.World-publication-check/1.1"
TIMEOUT = 20
RELEASE_MANIFEST = ROOT / "releases/ssa-ontology/v0.1.0/release-manifest.json"
INTEGRITY_RECEIPT = ROOT / "docs/website/hosted-artifact-integrity-runtime.json"

PAGES = [
    (
        "https://www.mcloughlin.world/",
        ["93", "17", "CC BY 4.0"],
    ),
    (
        "https://www.mcloughlin.world/glossaries/ssa-lexicon/",
        ["SSA", "0.1.0"],
    ),
    (
        "https://www.mcloughlin.world/glossaries/ssa-lexicon/browse/",
        ["Browse"],
    ),
    (
        "https://www.mcloughlin.world/glossaries/ssa-lexicon/downloads/",
        ["JSON-LD", "Turtle", "CSV"],
    ),
    (
        "https://www.mcloughlin.world/glossaries/ssa-lexicon/releases/",
        ["0.1.0"],
    ),
    (
        "https://www.mcloughlin.world/datasets/",
        ["Datasets", "SSA"],
    ),
]

# Only these release records currently have repository files that purport to
# represent the same published artefact byte-for-byte. The semantic data files
# and ZIP are site-export-derived reconstructions or externally hosted package
# artefacts; absence of an exact local copy must remain explicit.
EXACT_REPOSITORY_COPIES = {
    "release-manifest.json": RELEASE_MANIFEST,
    "CHANGELOG.md": ROOT / "releases/ssa-ontology/v0.1.0/CHANGELOG.md",
    "LICENSE.txt": ROOT / "releases/ssa-ontology/v0.1.0/LICENSE.txt",
    "README.md": ROOT / "releases/ssa-ontology/v0.1.0/README.md",
}


def fetch_bytes(url: str) -> tuple[int, str, bytes]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.getcode(), response.geturl(), response.read()


def fetch_text(url: str) -> tuple[int, str, str]:
    status, final_url, body = fetch_bytes(url)
    return status, final_url, body.decode("utf-8", errors="replace")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def zip_members_by_basename(zip_bytes: bytes) -> dict[str, bytes]:
    members: dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        for name in archive.namelist():
            if name.endswith("/"):
                continue
            basename = Path(name).name
            # Ambiguous duplicate basenames are intentionally excluded rather
            # than guessed into a false comparison.
            if basename in members:
                members.pop(basename, None)
                continue
            members[basename] = archive.read(name)
    return members


def verify_hosted_release_artifacts() -> tuple[list[str], dict]:
    failures: list[str] = []
    try:
        manifest = json.loads(RELEASE_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read canonical release manifest: {exc}"], {}

    public_root = manifest.get("publicFileRoot")
    declared = manifest.get("publishedArtifacts", [])
    if not isinstance(public_root, str) or not public_root.startswith("https://www.mcloughlin.world/"):
        return ["canonical release manifest has an invalid publicFileRoot"], {}
    if not isinstance(declared, list) or not declared:
        return ["canonical release manifest declares no published artifacts"], {}

    hosted: dict[str, bytes] = {}
    artifact_rows: list[dict] = []

    for item in declared:
        filename = item.get("filename") if isinstance(item, dict) else None
        if not isinstance(filename, str) or not filename:
            failures.append("release manifest contains an artifact without a filename")
            continue
        url = public_root.rstrip("/") + "/" + filename
        try:
            status, final_url, body = fetch_bytes(url)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            failures.append(f"{filename}: hosted retrieval failed: {exc}")
            continue
        if status != 200:
            failures.append(f"{filename}: expected HTTP 200, got {status}")
            continue
        if not final_url.startswith("https://www.mcloughlin.world/"):
            failures.append(f"{filename}: unexpected redirect target {final_url}")
            continue
        hosted[filename] = body

    zip_members: dict[str, bytes] = {}
    zip_name = "ssa-ontology-v0.1.0.zip"
    if zip_name in hosted:
        try:
            zip_members = zip_members_by_basename(hosted[zip_name])
        except (zipfile.BadZipFile, OSError) as exc:
            failures.append(f"{zip_name}: published package is not a readable ZIP: {exc}")

    exact_comparisons = 0
    exact_matches = 0
    exact_mismatches = 0
    package_comparisons = 0
    package_matches = 0
    package_mismatches = 0

    for item in declared:
        filename = item.get("filename") if isinstance(item, dict) else None
        if not isinstance(filename, str) or filename not in hosted:
            continue
        body = hosted[filename]
        row = {
            "filename": filename,
            "hosted_url": public_root.rstrip("/") + "/" + filename,
            "hosted_bytes": len(body),
            "hosted_sha256": sha256(body),
            "repository_exact_path": None,
            "repository_sha256": None,
            "repository_byte_identity": "NO_LOCAL_EXACT_COPY",
            "package_member_sha256": None,
            "package_member_identity": "NOT_APPLICABLE" if filename == zip_name else "NOT_PRESENT",
        }

        local_path = EXACT_REPOSITORY_COPIES.get(filename)
        if local_path is not None:
            row["repository_exact_path"] = str(local_path.relative_to(ROOT))
            if not local_path.exists():
                row["repository_byte_identity"] = "LOCAL_COPY_MISSING"
                failures.append(f"{filename}: expected exact repository copy is missing")
            else:
                local_bytes = local_path.read_bytes()
                row["repository_sha256"] = sha256(local_bytes)
                exact_comparisons += 1
                if local_bytes == body:
                    row["repository_byte_identity"] = "MATCH"
                    exact_matches += 1
                else:
                    row["repository_byte_identity"] = "MISMATCH"
                    exact_mismatches += 1
                    failures.append(
                        f"{filename}: hosted bytes differ from {local_path.relative_to(ROOT)}"
                    )

        if filename != zip_name and filename in zip_members:
            member = zip_members[filename]
            row["package_member_sha256"] = sha256(member)
            package_comparisons += 1
            if member == body:
                row["package_member_identity"] = "MATCH"
                package_matches += 1
            else:
                row["package_member_identity"] = "MISMATCH"
                package_mismatches += 1
                failures.append(f"{filename}: separately hosted bytes differ from published ZIP member")

        artifact_rows.append(row)

    local_exact_missing = sum(
        1 for row in artifact_rows if row["repository_byte_identity"] == "NO_LOCAL_EXACT_COPY"
    )
    full_repository_identity = (
        len(artifact_rows) == len(declared)
        and local_exact_missing == 0
        and exact_mismatches == 0
        and exact_matches == len(declared)
    )

    receipt = {
        "object_type": "ssa_hosted_artifact_integrity_receipt",
        "schema_version": "1.0.0",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "canonical_release": manifest.get("release"),
        "canonical_manifest": str(RELEASE_MANIFEST.relative_to(ROOT)),
        "public_file_root": public_root,
        "hash_algorithm": "SHA-256",
        "artifacts": artifact_rows,
        "summary": {
            "declared_artifacts": len(declared),
            "hosted_artifacts_retrieved": len(hosted),
            "exact_repository_comparisons": exact_comparisons,
            "exact_repository_matches": exact_matches,
            "exact_repository_mismatches": exact_mismatches,
            "no_local_exact_copy": local_exact_missing,
            "package_member_comparisons": package_comparisons,
            "package_member_matches": package_matches,
            "package_member_mismatches": package_mismatches,
            "full_repository_byte_identity_verified": full_repository_identity,
        },
        "status": "FAIL" if failures else ("VERIFIED" if full_repository_identity else "PARTIAL_VERIFIED"),
        "claim_boundaries": [
            "HOSTED_RETRIEVAL != REPOSITORY_BYTE_IDENTITY",
            "PACKAGE_MEMBER_MATCH != REPOSITORY_BYTE_IDENTITY",
            "NO_LOCAL_EXACT_COPY != MISMATCH",
            "PARTIAL_VERIFIED != FULL_RELEASE_BYTE_IDENTITY",
        ],
    }

    INTEGRITY_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    INTEGRITY_RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return failures, receipt


def main() -> None:
    failures: list[str] = []

    for url, markers in PAGES:
        try:
            status, final_url, body = fetch_text(url)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            failures.append(f"{url}: request failed: {exc}")
            continue

        if status != 200:
            failures.append(f"{url}: expected HTTP 200, got {status}")
            continue

        if not final_url.startswith("https://www.mcloughlin.world/"):
            failures.append(f"{url}: unexpected redirect target {final_url}")

        body_lower = body.lower()
        for marker in markers:
            if marker.lower() not in body_lower:
                failures.append(f"{url}: missing expected marker {marker!r}")

        print(f"OK {status} {url} -> {final_url}")

    integrity_failures, receipt = verify_hosted_release_artifacts()
    failures.extend(integrity_failures)
    if receipt:
        summary = receipt["summary"]
        print(
            "SSA hosted artifact integrity: "
            f"retrieved={summary['hosted_artifacts_retrieved']}/{summary['declared_artifacts']} "
            f"repo_matches={summary['exact_repository_matches']}/{summary['exact_repository_comparisons']} "
            f"zip_matches={summary['package_member_matches']}/{summary['package_member_comparisons']} "
            f"status={receipt['status']}"
        )
        print(f"Integrity receipt: {INTEGRITY_RECEIPT.relative_to(ROOT)}")

    if failures:
        print("Live-publication drift check failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        raise SystemExit(1)

    print("Live-publication drift check passed.")


if __name__ == "__main__":
    main()
