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
EXPECTED_REPOSITORY = "EduLinked-coder/McLoughlin.World"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read valid JSON from {path.relative_to(ROOT)}: {exc}")


def main() -> None:
    manifest_path = ROOT / "releases/ssa-ontology/v0.1.0/release-manifest.json"
    concepts_path = ROOT / "concepts/ssa-ontology-v0.1.0/README.md"
    root_readme_path = ROOT / "README.md"
    legacy_ssa_path = ROOT / "ssa/index.html"
    master_schema_path = ROOT / "_includes/ssa-master-schema.html"
    authority_path = ROOT / "docs/ECOSYSTEM-AUTHORITY.json"
    verification_path = ROOT / "docs/website/verification-status.json"
    release_citation_path = ROOT / "releases/ssa-ontology/v0.1.0/CITATION.cff"
    root_citation_path = ROOT / "CITATION.cff"
    licensing_path = ROOT / "docs/LICENSING.md"

    for path in (
        manifest_path,
        concepts_path,
        root_readme_path,
        legacy_ssa_path,
        master_schema_path,
        authority_path,
        verification_path,
        release_citation_path,
        root_citation_path,
        licensing_path,
    ):
        require(path.exists(), f"required publication file is missing: {path.relative_to(ROOT)}")

    manifest = read_json(manifest_path)
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

    authority = read_json(authority_path)
    require(authority.get("canonical_publication_repository") == EXPECTED_REPOSITORY, "ecosystem authority repository mismatch")
    require(authority.get("canonical_ontology") == CANONICAL_ONTOLOGY, "ecosystem authority canonical ontology mismatch")
    require(authority.get("new_repository_assessment", {}).get("required") is False, "ecosystem authority unexpectedly requires a new repository")
    precedence = authority.get("authority_precedence", [])
    require(precedence and precedence[0] == "current_live_canonical_public_page", "authority precedence must start with the current live canonical public page")
    require(all(item.get("may_override_public_release") is False for item in authority.get("repositories", [])), "an adjacent repository is incorrectly allowed to override the public release")

    verification = read_json(verification_path)
    require(verification.get("canonical_ontology") == CANONICAL_ONTOLOGY, "verification-status canonical ontology mismatch")
    require(verification.get("release") == EXPECTED_RELEASE, "verification-status release mismatch")
    require(verification.get("concept_count") == EXPECTED_CONCEPTS, "verification-status concept count mismatch")
    require(verification.get("scheme_count") == EXPECTED_SCHEMES, "verification-status scheme count mismatch")
    require(verification.get("hosted_artifact_integrity", {}).get("byte_identity_verified") is False, "verification status must not claim hosted byte identity before issue #3 is resolved")
    require(verification.get("repository_licensing", {}).get("software_or_tooling_license_resolved") is False, "software/tooling licence must remain unresolved until an explicit repository licence is chosen")

    release_citation = release_citation_path.read_text(encoding="utf-8")
    require('version: "0.1.0"' in release_citation, "release CITATION.cff version mismatch")
    require("date-released: 2026-07-29" in release_citation, "release CITATION.cff date mismatch")
    require('url: "https://www.mcloughlin.world/glossaries/ssa-lexicon/"' in release_citation, "release CITATION.cff canonical URL mismatch")
    require("license: CC-BY-4.0" in release_citation, "release CITATION.cff knowledge licence mismatch")

    root_citation = root_citation_path.read_text(encoding="utf-8")
    require('repository-code: "https://github.com/EduLinked-coder/McLoughlin.World"' in root_citation, "root CITATION.cff repository mismatch")
    require('version: "0.1.0"' in root_citation, "root CITATION.cff preferred release mismatch")
    require('license: "CC-BY-4.0"' in root_citation, "root CITATION.cff preferred citation licence mismatch")
    require("LicenseRef-Mixed-Pending-Software-License" not in root_citation, "root CITATION.cff must not invent an unresolved repository licence")

    licensing = licensing_path.read_text(encoding="utf-8")
    require("CC BY 4.0" in licensing, "licensing document does not record knowledge-content licence")
    require("GitHub currently detects no repository-level licence" in licensing, "licensing document does not preserve repository-licence uncertainty")
    require("must not be assumed to inherit CC BY 4.0" in licensing, "licensing document does not preserve code/content separation")

    print("Publication-state validation passed.")
    print(f"release={EXPECTED_RELEASE} concepts={EXPECTED_CONCEPTS} schemes={EXPECTED_SCHEMES}")
    print(f"canonical={CANONICAL_ONTOLOGY}")
    print("authority=validated verification_metadata=validated citations=validated licensing_boundary=validated")


if __name__ == "__main__":
    main()
