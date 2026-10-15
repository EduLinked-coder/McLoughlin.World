#!/usr/bin/env python3
"""Validate the repository mirror of the canonical coercive-control glossary.

This dependency-free check verifies repository-side integrity and metadata
alignment. It does not validate the live website, verify time-sensitive legal
sources, apply the JSON Schema, or replace human safeguarding/legal review.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "glossaries/glossary-of-coercive-control"
CANONICAL_URL = (
    "https://www.mcloughlin.world/glossaries/ssa-lexicon/"
    "glossary-of-coercive-control/"
)
HOSTED_ONLY_DISTRIBUTION = f"{CANONICAL_URL}glossary.json"
SHA_LINE = re.compile(r"^([0-9a-f]{64})  (\S+)$")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read valid JSON from {path.relative_to(ROOT)}: {exc}")
    require(isinstance(value, dict), f"{path.relative_to(ROOT)} must contain a JSON object")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest_path = PACKAGE / "manifest.json"
    checksums_path = PACKAGE / "checksums.json"
    sums_path = PACKAGE / "SHA256SUMS.txt"
    schema_path = PACKAGE / "schema.json"
    examples_path = PACKAGE / "examples.json"
    glossary_path = PACKAGE / "glossary.jsonld"

    for path in (
        manifest_path,
        checksums_path,
        sums_path,
        schema_path,
        examples_path,
        glossary_path,
    ):
        require(path.exists(), f"required package file is missing: {path.relative_to(ROOT)}")

    manifest = read_json(manifest_path)
    checksums = read_json(checksums_path)
    schema = read_json(schema_path)
    examples = read_json(examples_path)
    glossary = read_json(glossary_path)
    read_json(PACKAGE / "sources.json")

    require(
        manifest.get("object_type") == "glossary_distribution_manifest",
        "distribution manifest object type mismatch",
    )
    require(
        checksums.get("object_type") == "glossary_integrity_manifest",
        "integrity manifest object type mismatch",
    )
    require(manifest.get("status") == "canonical", "distribution manifest status mismatch")
    require(checksums.get("status") == "canonical", "integrity manifest status mismatch")
    require(
        manifest.get("vocabulary_version") == checksums.get("vocabulary_version") == "1.0.0",
        "manifest vocabulary versions are not aligned",
    )
    require(
        manifest.get("canonical_url") == CANONICAL_URL,
        "distribution manifest canonical URL mismatch",
    )
    require(
        checksums.get("canonical_glossary_url") == CANONICAL_URL,
        "integrity manifest canonical URL mismatch",
    )
    require(checksums.get("hash_algorithm") == "SHA-256", "unsupported hash algorithm")

    records = checksums.get("files")
    require(isinstance(records, list) and records, "integrity manifest files must be a non-empty array")

    published_names: set[str] = set()
    urls: set[str] = set()
    recorded_sums: dict[str, str] = {}
    mirrored_paths: set[str] = set()

    for index, record in enumerate(records):
        require(isinstance(record, dict), f"integrity record {index} must be an object")
        published_name = record.get("filename")
        url = record.get("url")
        expected_bytes = record.get("bytes")
        expected_hash = record.get("sha256")
        require(isinstance(published_name, str) and published_name, f"integrity record {index} has no filename")
        require(isinstance(url, str) and url.startswith(CANONICAL_URL), f"integrity record {published_name} has an invalid URL")
        require(isinstance(expected_bytes, int) and expected_bytes >= 0, f"integrity record {published_name} has invalid bytes")
        require(isinstance(expected_hash, str) and re.fullmatch(r"[0-9a-f]{64}", expected_hash) is not None, f"integrity record {published_name} has invalid SHA-256")
        require(published_name not in published_names, f"duplicate published filename: {published_name}")
        require(url not in urls, f"duplicate integrity URL: {url}")
        published_names.add(published_name)
        urls.add(url)
        recorded_sums[published_name] = expected_hash

        local_name = Path(urlparse(url).path).name
        require(local_name, f"cannot derive repository filename from URL: {url}")
        local_path = PACKAGE / local_name
        require(local_path.exists(), f"integrity URL has no repository mirror: {local_path.relative_to(ROOT)}")
        require(local_name not in mirrored_paths, f"duplicate repository mirror path: {local_name}")
        mirrored_paths.add(local_name)
        data = local_path.read_bytes()
        require(len(data) == expected_bytes, f"byte count mismatch for {local_path.relative_to(ROOT)}")
        require(hashlib.sha256(data).hexdigest() == expected_hash, f"SHA-256 mismatch for {local_path.relative_to(ROOT)}")

    text_sums: dict[str, str] = {}
    for line_number, raw_line in enumerate(sums_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line:
            continue
        match = SHA_LINE.fullmatch(raw_line)
        require(match is not None, f"invalid SHA256SUMS entry at line {line_number}")
        digest, published_name = match.groups()
        require(published_name not in text_sums, f"duplicate SHA256SUMS filename: {published_name}")
        text_sums[published_name] = digest
    require(text_sums == recorded_sums, "SHA256SUMS.txt does not match checksums.json")

    distributions = manifest.get("distributions")
    require(isinstance(distributions, list) and distributions, "distribution manifest has no distributions")
    distribution_urls = {
        item.get("url")
        for item in distributions
        if isinstance(item, dict) and isinstance(item.get("url"), str)
    }
    expected_mirrored_distributions = {
        f"{CANONICAL_URL}glossary.csv",
        f"{CANONICAL_URL}glossary.jsonld",
        f"{CANONICAL_URL}glossary.rdf",
        f"{CANONICAL_URL}glossary.ttl",
    }
    require(
        expected_mirrored_distributions.issubset(distribution_urls),
        "distribution manifest is missing a mirrored machine-readable format",
    )
    require(
        expected_mirrored_distributions.issubset(urls),
        "integrity manifest is missing a mirrored machine-readable distribution",
    )
    require(
        HOSTED_ONLY_DISTRIBUTION in distribution_urls,
        "distribution manifest no longer declares the hosted JSON representation",
    )
    require(
        HOSTED_ONLY_DISTRIBUTION not in urls and not (PACKAGE / "glossary.json").exists(),
        "hosted-only JSON boundary changed; update the repository mirror classification",
    )

    require(glossary.get("@id") == CANONICAL_URL, "JSON-LD canonical identifier mismatch")
    require(glossary.get("url") == CANONICAL_URL, "JSON-LD canonical URL mismatch")
    require(glossary.get("version") == "1.0.0", "JSON-LD vocabulary version mismatch")
    require(glossary.get("inLanguage") == "en-AU", "JSON-LD language mismatch")
    terms = glossary.get("hasDefinedTerm")
    require(isinstance(terms, list) and terms, "JSON-LD must contain defined terms")
    term_codes = [term.get("termCode") for term in terms if isinstance(term, dict)]
    require(len(term_codes) == len(terms), "every JSON-LD term must have a termCode")
    require(len(set(term_codes)) == len(term_codes), "JSON-LD contains duplicate termCode values")

    require(
        schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema",
        "schema draft mismatch",
    )
    require(schema.get("$id") == f"{CANONICAL_URL}schema.json", "schema canonical identifier mismatch")
    require(examples.get("canonical_url") == f"{CANONICAL_URL}examples.json", "examples canonical URL mismatch")
    require(examples.get("schema_url") == f"{CANONICAL_URL}schema.json", "examples schema URL mismatch")

    print("Coercive-control glossary package validation passed.")
    print(f"version={manifest['vocabulary_version']} integrity_files={len(records)} terms={len(terms)}")
    print(f"canonical={CANONICAL_URL}")
    print("boundary=repository_integrity_only hosted_json=not_mirrored_or_integrity_checked")


if __name__ == "__main__":
    main()
