#!/usr/bin/env python3
"""Read-only checks against the live McLoughlin.world publication surface.

This script detects drift between repository expectations and the public site.
It never changes canonical content and should be treated as a monitoring aid,
not as publication authority.

The SSA release-integrity check reuses the canonical release manifest and the
existing publication verification status. It records hosted SHA-256 hashes,
compares exact repository-side copies where they actually exist, compares
separately hosted artefacts with matching members inside the published ZIP, and
fails only on a new or changed integrity signature. A durably recorded mismatch
remains a mismatch; acknowledging it prevents routine monitoring from staying
red forever without falsely promoting byte identity.
"""

from __future__ import annotations

import hashlib
from html import unescape
import io
import json
import os
import re
import socket
import sys
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlsplit

ROOT = Path(__file__).resolve().parents[1]
USER_AGENT = "McLoughlin.World-publication-check/1.2"
TIMEOUT = 20
RELATED_SURFACE_TIMEOUT = 6
PUBLIC_METADATA_TIMEOUT = 5
RELEASE_MANIFEST = ROOT / "releases/ssa-ontology/v0.1.0/release-manifest.json"
VERIFICATION_STATUS = ROOT / "docs/website/verification-status.json"
INTEGRITY_RECEIPT = ROOT / "docs/website/hosted-artifact-integrity-runtime.json"

PAGES = [
    ("https://www.mcloughlin.world/", ["93", "17", "CC BY 4.0"]),
    ("https://www.mcloughlin.world/glossaries/ssa-lexicon/", ["SSA", "0.1.0"]),
    ("https://www.mcloughlin.world/glossaries/ssa-lexicon/browse/", ["Browse"]),
    (
        "https://www.mcloughlin.world/glossaries/ssa-lexicon/downloads/",
        ["JSON-LD", "Turtle", "CSV"],
    ),
    ("https://www.mcloughlin.world/glossaries/ssa-lexicon/releases/", ["0.1.0"]),
    ("https://www.mcloughlin.world/datasets/", ["Datasets", "SSA"]),
]

# These are observational targets, not approved Index Line publishing routes.
# The McLoughlin.world route originates in docs/website/OTHER-PUBLIC-SURFACES.md
# (7 August 2026 export). indexline.org remains independently unverified.
RELATED_INDEX_LINE_SURFACES = (
    ("mcloughlin_world_index_line_export_route", "https://www.mcloughlin.world/theindexline/"),
    ("indexline_org_unverified_domain", "https://indexline.org/"),
)

# Only these release records currently have repository files that are directly
# comparable to published artefacts. The semantic serialisations and ZIP have
# no local exact-copy representation; they remain explicitly unresolved rather
# than being compared with differently derived source/export files.
EXACT_REPOSITORY_COPIES = {
    "release-manifest.json": RELEASE_MANIFEST,
    "CHANGELOG.md": ROOT / "releases/ssa-ontology/v0.1.0/CHANGELOG.md",
    "LICENSE.txt": ROOT / "releases/ssa-ontology/v0.1.0/LICENSE.txt",
    "README.md": ROOT / "releases/ssa-ontology/v0.1.0/README.md",
}


def fetch_bytes(url: str, timeout: float = TIMEOUT) -> tuple[int, str, bytes]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.getcode(), response.geturl(), response.read()


def fetch_text(url: str, timeout: float = TIMEOUT) -> tuple[int, str, str]:
    status, final_url, body = fetch_bytes(url, timeout=timeout)
    return status, final_url, body.decode("utf-8", errors="replace")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def zip_members_by_basename(zip_bytes: bytes) -> dict[str, bytes]:
    members: dict[str, bytes] = {}
    duplicates: set[str] = set()
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        for name in archive.namelist():
            if name.endswith("/"):
                continue
            basename = Path(name).name
            if basename in members or basename in duplicates:
                members.pop(basename, None)
                duplicates.add(basename)
                continue
            members[basename] = archive.read(name)
    return members


def load_known_mismatches() -> dict[str, dict]:
    try:
        status = json.loads(VERIFICATION_STATUS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    integrity = status.get("hosted_artifact_integrity", {})
    rows = integrity.get("known_mismatches", [])
    if not isinstance(rows, list):
        return {}
    return {
        row.get("filename"): row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("filename"), str)
    }


def classify_difference(filename: str, hosted: bytes, local: bytes) -> str:
    if filename.lower().endswith(".json"):
        try:
            if json.loads(hosted.decode("utf-8")) == json.loads(local.decode("utf-8")):
                return "JSON_SERIALIZATION_ONLY"
            return "JSON_CONTENT_DIFFERENCE"
        except (UnicodeDecodeError, json.JSONDecodeError):
            return "BINARY_OR_UNPARSEABLE_DIFFERENCE"

    try:
        hosted_text = hosted.decode("utf-8")
        local_text = local.decode("utf-8")
    except UnicodeDecodeError:
        return "BINARY_DIFFERENCE"

    normalize = lambda value: re.sub(r"\s+", " ", value).strip()
    if normalize(hosted_text) == normalize(local_text):
        return "WHITESPACE_ONLY"
    return "TEXT_CONTENT_DIFFERENCE"


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

    known_mismatches = load_known_mismatches()
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
    acknowledged_mismatches = 0
    unacknowledged_mismatches = 0
    package_comparisons = 0
    package_matches = 0
    package_mismatches = 0

    for item in declared:
        filename = item.get("filename") if isinstance(item, dict) else None
        if not isinstance(filename, str) or filename not in hosted:
            continue
        body = hosted[filename]
        hosted_digest = sha256(body)
        row = {
            "filename": filename,
            "hosted_url": public_root.rstrip("/") + "/" + filename,
            "hosted_bytes": len(body),
            "hosted_sha256": hosted_digest,
            "repository_exact_path": None,
            "repository_sha256": None,
            "repository_byte_identity": "NO_LOCAL_EXACT_COPY",
            "difference_class": None,
            "package_member_sha256": None,
            "package_member_identity": "NOT_APPLICABLE" if filename == zip_name else "NOT_PRESENT",
        }

        local_path = EXACT_REPOSITORY_COPIES.get(filename)
        if local_path is not None:
            relative_path = str(local_path.relative_to(ROOT))
            row["repository_exact_path"] = relative_path
            if not local_path.exists():
                row["repository_byte_identity"] = "LOCAL_COPY_MISSING"
                failures.append(f"{filename}: expected exact repository copy is missing")
            else:
                local_bytes = local_path.read_bytes()
                local_digest = sha256(local_bytes)
                row["repository_sha256"] = local_digest
                exact_comparisons += 1
                if local_bytes == body:
                    row["repository_byte_identity"] = "MATCH"
                    exact_matches += 1
                else:
                    row["difference_class"] = classify_difference(filename, body, local_bytes)
                    expected = known_mismatches.get(filename, {})
                    signature_known = (
                        expected.get("repository_path") == relative_path
                        and expected.get("hosted_sha256") == hosted_digest
                        and expected.get("repository_sha256") == local_digest
                    )
                    if signature_known:
                        row["repository_byte_identity"] = "MISMATCH_ACKNOWLEDGED"
                        acknowledged_mismatches += 1
                    else:
                        row["repository_byte_identity"] = "MISMATCH_UNACKNOWLEDGED"
                        unacknowledged_mismatches += 1
                        failures.append(
                            f"{filename}: new hosted/repository mismatch signature at {relative_path}"
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
        and acknowledged_mismatches == 0
        and unacknowledged_mismatches == 0
        and exact_matches == len(declared)
    )

    if failures:
        receipt_status = "FAIL"
    elif full_repository_identity:
        receipt_status = "VERIFIED"
    elif acknowledged_mismatches:
        receipt_status = "KNOWN_MISMATCH_STABLE"
    else:
        receipt_status = "PARTIAL_VERIFIED"

    receipt = {
        "object_type": "ssa_hosted_artifact_integrity_receipt",
        "schema_version": "1.1.0",
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
            "acknowledged_repository_mismatches": acknowledged_mismatches,
            "unacknowledged_repository_mismatches": unacknowledged_mismatches,
            "no_local_exact_copy": local_exact_missing,
            "package_member_comparisons": package_comparisons,
            "package_member_matches": package_matches,
            "package_member_mismatches": package_mismatches,
            "full_repository_byte_identity_verified": full_repository_identity,
        },
        "status": receipt_status,
        "claim_boundaries": [
            "HOSTED_RETRIEVAL != REPOSITORY_BYTE_IDENTITY",
            "PACKAGE_MEMBER_MATCH != REPOSITORY_BYTE_IDENTITY",
            "ACKNOWLEDGED_MISMATCH != BYTE_IDENTITY",
            "NO_LOCAL_EXACT_COPY != MISMATCH",
            "KNOWN_MISMATCH_STABLE != FULL_RELEASE_BYTE_IDENTITY",
        ],
    }

    INTEGRITY_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    INTEGRITY_RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return failures, receipt


def fetch_public_json(url: str, timeout: float = PUBLIC_METADATA_TIMEOUT) -> dict:
    """Fetch public registry/DNS metadata; never collect registrant contact data."""
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object")
    return payload


def lookup_domain_registry_and_dns(host: str) -> dict:
    """Independently observe RDAP registration and NS/MX DNS answers.

    No result establishes the domain owner's authority, working email delivery,
    an Oncord tenant, renewal payment or editorial rights.
    """
    result = {
        "registration_rdap": "UNKNOWN",
        "rdap_expiry_event": None,
        "dns_ns": "UNKNOWN",
        "dns_mx": "UNKNOWN",
        "dns_ns_answers": [],
        "dns_mx_answers": [],
    }
    try:
        # .org registry endpoint verified in IANA's current root record.
        # RDAP observations never prove registrar-account control or renewal.
        rdap = fetch_public_json(
            f"https://rdap.publicinterestregistry.org/rdap/domain/{host}"
        )
        # An arbitrary JSON response with a matching ldhName is not a
        # validated domain RDAP object (IANA RDAP conformance requirement).
        if (rdap.get("objectClassName") == "domain"
                and isinstance(rdap.get("ldhName"), str)
                and rdap["ldhName"].lower().rstrip(".") == host):
            result["registration_rdap"] = "RDAP_RECORD_OBSERVED"
            for event in (rdap.get("events") if isinstance(rdap.get("events"), list) else []):
                if (
                    isinstance(event, dict)
                    and event.get("eventAction") == "expiration"
                    and isinstance(event.get("eventDate"), str)
                ):
                    date = event["eventDate"]
                    try:
                        parsed = datetime.fromisoformat(date.replace("Z", "+00:00"))
                    except ValueError:
                        continue
                    if parsed.tzinfo is None:
                        continue
                    result["rdap_expiry_event"] = date
                    break
        else:
            result["registration_rdap"] = "RDAP_RESPONSE_IDENTITY_UNVERIFIED"
    except urllib.error.HTTPError as exc:
        # A registry 404 does not establish domain expiry or registrar ownership.
        result["registration_rdap"] = (
            "RDAP_404_NO_RECORD_NOT_REGISTRAR_PROOF" if exc.code == 404
            else "RDAP_LOOKUP_FAILED_NOT_PROOF_OF_EXPIRY"
        )
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        result["registration_rdap"] = "RDAP_LOOKUP_FAILED_NOT_PROOF_OF_EXPIRY"

    for label, record_type in (("ns", 2), ("mx", 15)):
        try:
            data = fetch_public_json(
                "https://dns.google/resolve?" + urlencode({
                    "name": host, "type": label.upper()
                })
            )
            if data.get("Status") == 3:
                result[f"dns_{label}"] = "NXDOMAIN_RESPONSE_NOT_REGISTRAR_PROOF"
            elif data.get("Status") == 0:
                answers = [
                    item.get("data")
                    for item in (data.get("Answer") if isinstance(data.get("Answer"), list) else [])
                    if isinstance(item, dict)
                    and item.get("type") == record_type
                    and isinstance(item.get("data"), str)
                ]
                result[f"dns_{label}"] = (
                    "RECORDS_OBSERVED" if answers else "NO_MATCHING_ANSWERS_OBSERVED"
                )
                result[f"dns_{label}_answers"] = answers[:20]
            else:
                result[f"dns_{label}"] = "DNS_RESPONSE_INCONCLUSIVE"
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            result[f"dns_{label}"] = "DNS_LOOKUP_FAILED"
    return result


def has_index_line_page_identity(body: str) -> bool:
    """Find an identifying page title or heading, not an unrelated footer link.

    A matching heading is a diagnostic observation only. It is not proof of
    editorial approval, ownership, Oncord connection or publication authority.
    """
    for match in re.finditer(r"(?is)<(title|h1|h2)\b[^>]*>(.*?)</\1>", body):
        label = unescape(re.sub(r"(?s)<[^>]*>", " ", match.group(2)))
        if re.search(r"\bthe\s+index\s+line\b", label, flags=re.IGNORECASE):
            return True
    return False


def observe_related_public_surfaces(
    targets: tuple[tuple[str, str], ...] = RELATED_INDEX_LINE_SURFACES,
) -> list[dict]:
    """Bounded, read-only observations; no claim of ownership or publication approval.

    DNS address resolution is independent of an HTTP response. Neither confirms
    domain registration/renewal, MX/email service, Oncord, rights or editorial
    release. Failures here are informative and never change the SSA release gate.
    """
    observations = []
    for surface_id, url in targets:
        host = urlsplit(url).hostname
        row = {
            "surface_id": surface_id,
            "url": url,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "address_resolution": "UNKNOWN",
            "http_status": None,
            "final_url": None,
            "http_observation": "UNKNOWN",
            "registration": "UNKNOWN",
            "mail_mx_and_delivery": "UNKNOWN",
            "oncord_connection": "UNKNOWN",
            "editorial_approval": "NOT_VERIFIED",
            "publication_authorisation": "NOT_VERIFIED",
        }
        try:
            socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
            row["address_resolution"] = "RESOLVED"
        except (socket.gaierror, OSError):
            row["address_resolution"] = "LOOKUP_FAILED_NOT_PROOF_OF_EXPIRY"

        try:
            status, final_url, body = fetch_text(url, timeout=RELATED_SURFACE_TIMEOUT)
            row["http_status"] = status
            row["final_url"] = final_url
            if (
                status == 200
                and urlsplit(final_url).scheme == "https"
                and urlsplit(final_url).hostname == host
                # A same-host redirect to a different page is not route parity,
                # even when the destination mentions The Index Line.
                and urlsplit(final_url).path.rstrip("/") == urlsplit(url).path.rstrip("/")
                and has_index_line_page_identity(body)
            ):
                row["http_observation"] = "HTTP_200_EXPECTED_MARKER_OBSERVED"
            else:
                row["http_observation"] = "RESPONSE_NOT_SUFFICIENT_FOR_ROUTE_MATCH"
        except urllib.error.HTTPError as exc:
            row["http_status"] = exc.code
            row["final_url"] = exc.geturl()
            row["http_observation"] = "HTTP_NON_200"
        except (urllib.error.URLError, TimeoutError, OSError):
            row["http_observation"] = "FETCH_FAILED_NOT_PROOF_OF_DOMAIN_STATUS"
        if host == "indexline.org":
            row.update(lookup_domain_registry_and_dns(host))
        observations.append(row)
    return observations



def append_index_line_actions_summary(observations: list[dict]) -> None:
    """Make existing Actions run evidence skimmable without another receipt store.

    Only fixed, bounded observation fields enter the native job summary. Never
    copy registrant data, HTML, untrusted URLs, or protected editorial material.
    An absent or unwritable summary must not alter the SSA release gate.
    """
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    def bounded(value: object) -> str:
        if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_]{1,90}", value):
            return value
        return "UNKNOWN"

    columns = (
        "surface_id", "address_resolution", "http_observation",
        "registration_rdap", "dns_ns", "dns_mx", "oncord_connection",
        "editorial_approval", "publication_authorisation",
    )
    lines = [
        "### The Index Line — read-only publishing surface observations",
        "",
        "| Surface | Address | HTTP route | RDAP | DNS NS | DNS MX | Oncord | Editorial | Publication |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in observations:
        if isinstance(row, dict):
            lines.append("| " + " | ".join(bounded(row.get(key)) for key in columns) + " |")
    lines.extend([
        "",
        "A responding page is **not** an approved article. DNS/RDAP results cannot "
        "establish registrar account control, payment or renewal; MX cannot prove "
        "email delivery. Oncord tenant, named Lead Editor, author rights, "
        "source protection, editorial and publication permissions require "
        "their separate authorised readbacks. **UNKNOWN != PASS.**",
        "",
        "Technical checks use this existing GitHub Actions job; scheduled/main "
        "runs retain the separate existing integrity receipt.",
        "",
    ])
    try:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write("\n".join(lines) + "\n")
    except OSError as exc:
        print(f"Actions summary unavailable: {type(exc).__name__}", file=sys.stderr)


def verify_index_line_receipt_readback(path: Path = INTEGRITY_RECEIPT) -> list[str]:
    """Independently read back the existing scheduled/main receipt after writing.

    Match source revision and run ID against GitHub-provided execution context.
    This is technical receipt integrity only, never evidence or editorial approval.
    Do not trigger another network lookup or write another tracking object.
    """
    failures: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ["existing hosted integrity receipt is missing or unreadable"]
    if not isinstance(payload, dict) or payload.get("object_type") != "ssa_hosted_artifact_integrity_receipt":
        return ["existing hosted integrity receipt has unexpected object type"]
    related = payload.get("related_index_line_observations")
    if not isinstance(related, dict):
        return ["existing receipt has no Index Line observation section"]

    expected_sha = os.environ.get("GITHUB_SHA", "")
    expected_run = os.environ.get("GITHUB_RUN_ID", "")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", expected_sha):
        failures.append("trusted GitHub source revision is missing or invalid")
    elif related.get("source_revision") != expected_sha:
        failures.append("recorded source revision does not match executing revision")
    if not re.fullmatch(r"[0-9]+", expected_run):
        failures.append("trusted GitHub run ID is missing or invalid")
    elif related.get("run_id") != expected_run:
        failures.append("recorded run ID does not match executing run")
    if related.get("source") != "docs/website/OTHER-PUBLIC-SURFACES.md":
        failures.append("Index Line route source is not the established site-export manifest")

    observed = related.get("observations")
    if not isinstance(observed, list):
        return failures + ["Index Line observation population is absent or invalid"]
    expected_surfaces = dict(RELATED_INDEX_LINE_SURFACES)
    seen: set[str] = set()
    for item in observed:
        if not isinstance(item, dict):
            failures.append("Index Line observation row is not a mapping")
            continue
        surface = item.get("surface_id")
        if not isinstance(surface, str) or surface not in expected_surfaces or surface in seen:
            failures.append("Index Line observation has an unexpected or duplicate identity")
            continue
        seen.add(surface)
        if item.get("url") != expected_surfaces[surface]:
            failures.append(f"{surface}: observed URL differs from the known diagnostic target")
        # Bound the public-route evidence vocabulary as strictly as the domain
        # metadata. Otherwise a retained receipt could claim a successful live
        # route using a contradictory status or unrelated redirect destination.
        timestamp = item.get("observed_at")
        try:
            if not isinstance(timestamp, str) or datetime.fromisoformat(
                timestamp.replace("Z", "+00:00")
            ).tzinfo is None:
                raise ValueError("timestamp must be timezone-aware")
        except ValueError:
            failures.append(f"{surface}: observation timestamp missing or invalid")
        if item.get("address_resolution") not in {
            "RESOLVED", "LOOKUP_FAILED_NOT_PROOF_OF_EXPIRY",
        }:
            failures.append(f"{surface}: address observation is not an allowed public status")
        http_observation = item.get("http_observation")
        http_status = item.get("http_status")
        final_url = item.get("final_url")
        if http_observation not in {
            "HTTP_200_EXPECTED_MARKER_OBSERVED",
            "RESPONSE_NOT_SUFFICIENT_FOR_ROUTE_MATCH",
            "HTTP_NON_200",
            "FETCH_FAILED_NOT_PROOF_OF_DOMAIN_STATUS",
        }:
            failures.append(f"{surface}: HTTP observation is not an allowed public status")
        elif http_observation == "HTTP_200_EXPECTED_MARKER_OBSERVED":
            expected = urlsplit(expected_surfaces[surface])
            actual = urlsplit(final_url) if isinstance(final_url, str) else None
            if (
                type(http_status) is not int or http_status != 200
                or actual is None or actual.scheme != "https"
                or actual.hostname != expected.hostname
                or actual.path.rstrip("/") != expected.path.rstrip("/")
            ):
                failures.append(f"{surface}: successful HTTP route observation contradicts response")
        elif http_observation == "HTTP_NON_200":
            if type(http_status) is not int or not 300 <= http_status <= 599:
                failures.append(f"{surface}: non-success HTTP observation contradicts response")
        elif http_observation == "FETCH_FAILED_NOT_PROOF_OF_DOMAIN_STATUS":
            if http_status is not None or final_url is not None:
                failures.append(f"{surface}: failed HTTP fetch contradicts response")
        # Technical diagnostics must never be converted into editorial or Oncord approvals.
        if (item.get("oncord_connection") != "UNKNOWN"
                or item.get("editorial_approval") != "NOT_VERIFIED"
                or item.get("publication_authorisation") != "NOT_VERIFIED"):
            failures.append(f"{surface}: protected authority boundary changed")
        # A byte-identical receipt is not a registration, email, or DNS
        # authority grant. Refuse unexpected status labels (or missing fields)
        # before a downstream reader can mistake them for verified services.
        if (item.get("registration") != "UNKNOWN"
                or item.get("mail_mx_and_delivery") != "UNKNOWN"):
            failures.append(f"{surface}: domain or email authority boundary changed")
        if surface == "indexline_org_unverified_domain":
            rdap_observations = {
                "RDAP_RECORD_OBSERVED",
                "RDAP_RESPONSE_IDENTITY_UNVERIFIED",
                "RDAP_404_NO_RECORD_NOT_REGISTRAR_PROOF",
                "RDAP_LOOKUP_FAILED_NOT_PROOF_OF_EXPIRY",
            }
            dns_observations = {
                "RECORDS_OBSERVED",
                "NO_MATCHING_ANSWERS_OBSERVED",
                "NXDOMAIN_RESPONSE_NOT_REGISTRAR_PROOF",
                "DNS_RESPONSE_INCONCLUSIVE",
                "DNS_LOOKUP_FAILED",
            }
            if item.get("registration_rdap") not in rdap_observations:
                failures.append(f"{surface}: registry observation is not an allowed public status")
            for record in ("ns", "mx"):
                status = item.get(f"dns_{record}")
                if status not in dns_observations:
                    failures.append(
                        f"{surface}: DNS {record.upper()} observation is not an allowed public status"
                    )
                answers = item.get(f"dns_{record}_answers")
                if (not isinstance(answers, list)
                        or len(answers) > 20
                        or any(not isinstance(answer, str) or not answer.strip()
                               or len(answer) > 512 for answer in answers)):
                    failures.append(f"{surface}: DNS {record.upper()} answers are invalid")
                elif (status == "RECORDS_OBSERVED") != bool(answers):
                    failures.append(f"{surface}: DNS {record.upper()} status and answers contradict")
            # Public expiry metadata is meaningful only alongside a matching
            # registry record; a 404/failure must never carry an expiry claim.
            expiry = item.get("rdap_expiry_event")
            if expiry is not None:
                valid_timestamp = False
                if isinstance(expiry, str):
                    try:
                        valid_timestamp = datetime.fromisoformat(
                            expiry.replace("Z", "+00:00")
                        ).tzinfo is not None
                    except ValueError:
                        pass
                if (item.get("registration_rdap") != "RDAP_RECORD_OBSERVED"
                        or not valid_timestamp):
                    failures.append(f"{surface}: registry expiry contradicts observation")
    if seen != set(expected_surfaces):
        failures.append("Index Line diagnostic observation population is incomplete")
    return failures


def run_index_line_receipt_readback(path: Path = INTEGRITY_RECEIPT) -> None:
    """Fail closed on corrupt or misattributed producer OR downloaded receipts."""
    problems = verify_index_line_receipt_readback(path)
    if problems:
        for problem in problems:
            print(f"Index Line receipt readback failed: {problem}", file=sys.stderr)
        raise SystemExit(1)
    print("Index Line receipt readback passed: source SHA, run ID, targets, protected gates.")


def show_related_index_line_observations() -> None:
    """Print safe public diagnostics to the existing Actions job log.

    This does not execute the SSA hosted-release check, produce a new
    publisher record, or approve any article or domain configuration.
    """
    observations = observe_related_public_surfaces()
    append_index_line_actions_summary(observations)
    print(json.dumps({
        "purpose": "read_only_index_line_public_surface_diagnostics",
        "observations": observations,
        "claim_boundary": (
            "HTTP_OR_DNS_OR_RDAP != EDITORIAL_APPROVAL; "
            "MX != EMAIL_DELIVERY; WEBSITE != ONCORD_CONNECTION; UNKNOWN != PASS"
        ),
    }, indent=2))


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
    # Public route observations have independent diagnostic value even when a
    # missing/corrupt SSA release manifest prevents an integrity receipt.
    # Keep SSA failure fatal; never present these observations as release approval.
    related_observations = observe_related_public_surfaces()
    append_index_line_actions_summary(related_observations)
    for item in related_observations:
        print(
            f"Index Line diagnostic {item['surface_id']}: "
            f"address={item['address_resolution']} http={item['http_observation']}"
        )
    if receipt:
        receipt["related_index_line_observations"] = {
            "purpose": "non_authoritative_public_route_diagnostics",
            "source": "docs/website/OTHER-PUBLIC-SURFACES.md",
            # These identify the existing Actions run and tested source revision.
            # They are technical provenance, never an editorial or domain approval.
            "source_revision": (
                os.environ.get("GITHUB_SHA")
                if re.fullmatch(r"[0-9a-fA-F]{40}", os.environ.get("GITHUB_SHA", ""))
                else None
            ),
            "run_id": (
                os.environ.get("GITHUB_RUN_ID")
                if os.environ.get("GITHUB_RUN_ID", "").isdigit()
                else None
            ),
            "observations": related_observations,
            "claim_boundary": (
                "RDAP_OR_DNS_ANSWERS != REGISTRANT_AUTHORITY_OR_RENEWAL_PAYMENT; "
                "DNS_MX_RECORD != FUNCTIONING_EMAIL; "
                "HTTP_PAGE_MARKER != EDITORIAL_APPROVAL_OR_ONCORD_PUBLICATION; "
                "UNKNOWN != PASS"
            ),
        }
        INTEGRITY_RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        summary = receipt["summary"]
        print(
            "SSA hosted artifact integrity: "
            f"retrieved={summary['hosted_artifacts_retrieved']}/{summary['declared_artifacts']} "
            f"repo_matches={summary['exact_repository_matches']}/{summary['exact_repository_comparisons']} "
            f"acknowledged_mismatches={summary['acknowledged_repository_mismatches']} "
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
    if sys.argv[1:] == ["--related-index-line-only"]:
        show_related_index_line_observations()
    elif sys.argv[1:] == ["--verify-index-line-receipt"]:
        run_index_line_receipt_readback()
    elif len(sys.argv) == 3 and sys.argv[1] == "--verify-index-line-receipt-file":
        # Verify a previously downloaded artifact in-place; no network access,
        # new registry, or authority transition is involved.
        run_index_line_receipt_readback(Path(sys.argv[2]))
    elif len(sys.argv) == 1:
        main()
    else:
        raise SystemExit(
            "Usage: check_live_publication.py "
            "[--related-index-line-only|--verify-index-line-receipt|"
            "--verify-index-line-receipt-file PATH]"
        )
