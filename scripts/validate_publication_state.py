#!/usr/bin/env python3
"""Validate core McLoughlin.world publication invariants.

This validator is intentionally dependency-free. It checks repository-side
publication metadata only; it does not claim to validate the live website or
replace human review of releases, licensing, safeguarding, or legal content.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_ONTOLOGY = "https://www.mcloughlin.world/glossaries/ssa-lexicon/"
EXPECTED_RELEASE = "0.1.0"
EXPECTED_DATE = "2026-07-29"
EXPECTED_CONCEPTS = 93
EXPECTED_SCHEMES = 17
EXPECTED_LICENSE = "https://creativecommons.org/licenses/by/4.0/"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def main() -> None:
    manifest_path = ROOT / "releases/ssa-ontology/v0.1.0/release-manifest.json"
    concepts_path = ROOT / "concepts/ssa-ontology-v0.1.0/README.md"
    root_readme_path = ROOT / "README.md"
    legacy_ssa_path = ROOT / "ssa/index.html"
    master_schema_path = ROOT / "_includes/ssa-master-schema.html"

    for path in (
        manifest_path,
        concepts_path,
        root_readme_path,
        legacy_ssa_path,
        master_schema_path,
    ):
        require(path.exists(), f"required publication file is missing: {path.relative_to(ROOT)}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(manifest.get("release") == EXPECTED_RELEASE, "release version mismatch")
    require(manifest.get("datePublished") == EXPECTED_DATE, "release date mismatch")
    require(manifest.get("canonicalOntology") == CANONICAL_ONTOLOGY, "canonical ontology mismatch")
    require(manifest.get("conceptCount") == EXPECTED_CONCEPTS, "concept count mismatch")
    require(manifest.get("schemeCount") == EXPECTED_SCHEMES, "scheme count mismatch")
    require(manifest.get("license") == EXPECTED_LICENSE, "knowledge licence mismatch")

    representation = manifest.get("repositoryRepresentation", {})
    require(
        representation.get("byteIdentityWithHostedFilesVerified") is False,
        "hosted-file byte identity must remain false until hashes are independently verified",
    )

    artifacts = manifest.get("publishedArtifacts", [])
    artifact_names = {item.get("filename") for item in artifacts}
    expected_artifacts = {
        "ssa-ontology-v0.1.0.zip",
        "ssa-ontology.jsonld",
        "ssa-ontology.ttl",
        "ssa-ontology.rdf",
        "ssa-ontology.json",
        "ssa-terms.csv",
        "release-manifest.json",
        "CHANGELOG.md",
        "LICENSE.txt",
        "README.md",
    }
    require(expected_artifacts.issubset(artifact_names), "release manifest is missing published artefact declarations")

    concepts_text = concepts_path.read_text(encoding="utf-8")
    term_links = re.findall(
        r"^- \[[^\]]+\]\(https://www\.mcloughlin\.world/glossaries/ssa-lexicon/term/[^)]+/\)",
        concepts_text,
        flags=re.MULTILINE,
    )
    require(len(term_links) == EXPECTED_CONCEPTS, f"concept registry has {len(term_links)} canonical term links, expected {EXPECTED_CONCEPTS}")

    slugs = re.findall(
        r"https://www\.mcloughlin\.world/glossaries/ssa-lexicon/term/([^/]+)/",
        concepts_text,
    )
    require(len(slugs) == EXPECTED_CONCEPTS, "concept registry slug count mismatch")
    require(len(set(slugs)) == EXPECTED_CONCEPTS, "concept registry contains duplicate canonical term slugs")

    root_readme = root_readme_path.read_text(encoding="utf-8")
    require(CANONICAL_ONTOLOGY in root_readme, "root README does not declare current canonical ontology")
    require("legacy repository route `/ssa/`" in root_readme, "root README does not mark /ssa/ as legacy compatibility")

    legacy_ssa = legacy_ssa_path.read_text(encoding="utf-8").lower()
    require("canonical entry point" not in legacy_ssa, "legacy /ssa/ page still claims to be canonical")
    require("compatibility" in legacy_ssa, "legacy /ssa/ page is not explicitly labelled compatibility")

    master_schema = master_schema_path.read_text(encoding="utf-8")
    require(CANONICAL_ONTOLOGY in master_schema, "master JSON-LD does not reference the canonical ontology root")
    require('"version": "0.1.0"' in master_schema, "master JSON-LD release version mismatch")
    require('"license": "https://creativecommons.org/licenses/by/4.0/"' in master_schema, "master JSON-LD licence mismatch")

    print("Publication-state validation passed.")
    print(f"release={EXPECTED_RELEASE} concepts={EXPECTED_CONCEPTS} schemes={EXPECTED_SCHEMES}")
    print(f"canonical={CANONICAL_ONTOLOGY}")


if __name__ == "__main__":
    main()
