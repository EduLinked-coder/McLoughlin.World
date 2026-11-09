"""Offline regression tests for the existing live-publication checker.

Only read-only public route observations are covered. These tests never
authorise editorial release or classify domain renewal from DNS/HTTP.
"""

import io
import json
import socket
import subprocess
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import urllib.error
from unittest.mock import patch

from scripts import check_live_publication as checker


class RelatedIndexLineSurfaceTests(unittest.TestCase):
    def test_http_marker_is_observation_not_publication_approval(self):
        url = "https://www.mcloughlin.world/theindexline/"
        with (
            patch.object(checker.socket, "getaddrinfo", return_value=[("ok",)]),
            patch.object(checker, "fetch_text", return_value=(200, url, "<h1>The Index Line</h1>")),
        ):
            rows = checker.observe_related_public_surfaces((("historic_route", url),))
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["address_resolution"], "RESOLVED")
        self.assertEqual(row["http_observation"], "HTTP_200_EXPECTED_MARKER_OBSERVED")
        self.assertEqual(row["registration"], "UNKNOWN")
        self.assertEqual(row["mail_mx_and_delivery"], "UNKNOWN")
        self.assertEqual(row["oncord_connection"], "UNKNOWN")
        self.assertEqual(row["editorial_approval"], "NOT_VERIFIED")
        self.assertEqual(row["publication_authorisation"], "NOT_VERIFIED")

    def test_redirect_to_unrelated_host_does_not_verify_original_route(self):
        url = "https://indexline.org/"
        with (
            patch.object(checker.socket, "getaddrinfo", return_value=[("ok",)]),
            patch.object(checker, "fetch_text", return_value=(200, "https://example.org/", "The Index Line")),
            patch.object(checker, "lookup_domain_registry_and_dns", return_value={"registration_rdap": "UNKNOWN"}),
        ):
            row = checker.observe_related_public_surfaces((("candidate", url),))[0]
        self.assertEqual(row["http_observation"], "RESPONSE_NOT_SUFFICIENT_FOR_ROUTE_MATCH")
        self.assertEqual(row["oncord_connection"], "UNKNOWN")

    def test_same_host_wrong_path_redirect_does_not_verify_requested_route(self):
        url = "https://www.mcloughlin.world/theindexline/"
        redirected = "https://www.mcloughlin.world/publications/"
        with (
            patch.object(checker.socket, "getaddrinfo", return_value=[("ok",)]),
            patch.object(checker, "fetch_text", return_value=(200, redirected, "<h1>The Index Line</h1>")),
        ):
            row = checker.observe_related_public_surfaces((("historic_route", url),))[0]
        self.assertEqual(row["http_status"], 200)
        self.assertEqual(row["final_url"], redirected)
        self.assertEqual(row["http_observation"], "RESPONSE_NOT_SUFFICIENT_FOR_ROUTE_MATCH")
        self.assertEqual(row["publication_authorisation"], "NOT_VERIFIED")

    def test_same_path_trailing_slash_normalisation_remains_observational(self):
        url = "https://www.mcloughlin.world/theindexline/"
        with (
            patch.object(checker.socket, "getaddrinfo", return_value=[("ok",)]),
            patch.object(
                checker, "fetch_text",
                return_value=(200, "https://www.mcloughlin.world/theindexline", "<h1>The Index Line</h1>"),
            ),
        ):
            row = checker.observe_related_public_surfaces((("historic_route", url),))[0]
        self.assertEqual(row["http_observation"], "HTTP_200_EXPECTED_MARKER_OBSERVED")
        self.assertEqual(row["oncord_connection"], "UNKNOWN")
        self.assertEqual(row["editorial_approval"], "NOT_VERIFIED")

    def test_failures_do_not_prove_expiry_or_change_authority(self):
        url = "https://indexline.org/"
        with (
            patch.object(checker.socket, "getaddrinfo", side_effect=socket.gaierror("lookup failed")),
            patch.object(checker, "fetch_text", side_effect=urllib.error.URLError("unavailable")),
            patch.object(checker, "lookup_domain_registry_and_dns", return_value={"registration_rdap": "UNKNOWN"}),
        ):
            row = checker.observe_related_public_surfaces((("candidate", url),))[0]
        self.assertEqual(row["address_resolution"], "LOOKUP_FAILED_NOT_PROOF_OF_EXPIRY")
        self.assertEqual(row["http_observation"], "FETCH_FAILED_NOT_PROOF_OF_DOMAIN_STATUS")
        self.assertEqual(row["registration"], "UNKNOWN")
        self.assertEqual(row["publication_authorisation"], "NOT_VERIFIED")

    def test_non_200_is_not_a_success(self):
        url = "https://indexline.org/"
        error = urllib.error.HTTPError(url, 404, "Not Found", {}, None)
        with (
            patch.object(checker.socket, "getaddrinfo", return_value=[("ok",)]),
            patch.object(checker, "fetch_text", side_effect=error),
            patch.object(checker, "lookup_domain_registry_and_dns", return_value={"registration_rdap": "UNKNOWN"}),
        ):
            row = checker.observe_related_public_surfaces((("candidate", url),))[0]
        self.assertEqual(row["http_status"], 404)
        self.assertEqual(row["http_observation"], "HTTP_NON_200")


    def test_public_rdap_and_dns_are_distinct_from_delivery_or_oncord(self):
        def public_response(url):
            if "rdap.publicinterestregistry.org/rdap/domain/" in url:
                return {
                    "ldhName": "INDEXLINE.ORG",
                    "events": [{"eventAction": "expiration", "eventDate": "2027-07-04T00:00:00Z"}],
                }
            if "type=NS" in url:
                return {"Status": 0, "Answer": [{"type": 2, "data": "ns1.example.net."}]}
            if "type=MX" in url:
                return {"Status": 0, "Answer": [{"type": 15, "data": "10 mx.example.net."}]}
            raise AssertionError(f"Unexpected public-only query: {url}")

        with patch.object(checker, "fetch_public_json", side_effect=public_response) as fetch:
            details = checker.lookup_domain_registry_and_dns("indexline.org")
        self.assertEqual(fetch.call_count, 3)
        self.assertEqual(details["registration_rdap"], "RDAP_RECORD_OBSERVED")
        self.assertEqual(details["rdap_expiry_event"], "2027-07-04T00:00:00Z")
        self.assertEqual(details["dns_ns"], "RECORDS_OBSERVED")
        self.assertEqual(details["dns_mx"], "RECORDS_OBSERVED")
        self.assertEqual(details["dns_ns_answers"], ["ns1.example.net."])
        self.assertEqual(details["dns_mx_answers"], ["10 mx.example.net."])
        self.assertNotIn("mail_delivery_verified", details)

    def test_registry_404_does_not_establish_expiry_or_renewal(self):
        def public_response(url):
            if "rdap.publicinterestregistry.org/rdap/domain/" in url:
                raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
            return {"Status": 3}

        with patch.object(checker, "fetch_public_json", side_effect=public_response) as fetch:
            details = checker.lookup_domain_registry_and_dns("indexline.org")
        self.assertEqual(fetch.call_count, 3)
        self.assertEqual(
            fetch.call_args_list[0].args[0],
            "https://rdap.publicinterestregistry.org/rdap/domain/indexline.org",
        )
        self.assertEqual(details["registration_rdap"], "RDAP_404_NO_RECORD_NOT_REGISTRAR_PROOF")
        self.assertIsNone(details["rdap_expiry_event"])
        self.assertEqual(details["dns_ns"], "NXDOMAIN_RESPONSE_NOT_REGISTRAR_PROOF")

    def test_registry_http_503_remains_inconclusive(self):
        def public_response(url):
            if "rdap.publicinterestregistry.org/rdap/domain/" in url:
                raise urllib.error.HTTPError(url, 503, "Unavailable", {}, None)
            return {"Status": 0, "Answer": None}

        with patch.object(checker, "fetch_public_json", side_effect=public_response):
            details = checker.lookup_domain_registry_and_dns("indexline.org")
        self.assertEqual(details["registration_rdap"], "RDAP_LOOKUP_FAILED_NOT_PROOF_OF_EXPIRY")
        self.assertEqual(details["dns_ns"], "NO_MATCHING_ANSWERS_OBSERVED")

    def test_public_registry_and_dns_fail_closed(self):
        with patch.object(
            checker, "fetch_public_json", side_effect=urllib.error.URLError("offline")
        ):
            details = checker.lookup_domain_registry_and_dns("indexline.org")
        self.assertEqual(details["registration_rdap"], "RDAP_LOOKUP_FAILED_NOT_PROOF_OF_EXPIRY")
        self.assertEqual(details["dns_ns"], "DNS_LOOKUP_FAILED")
        self.assertEqual(details["dns_mx"], "DNS_LOOKUP_FAILED")
        self.assertIsNone(details["rdap_expiry_event"])

    def test_missing_dns_answers_and_rdap_events_do_not_crash(self):
        def public_response(url):
            if "rdap.publicinterestregistry.org/rdap/domain/" in url:
                return {"ldhName": "indexline.org", "events": None}
            return {"Status": 0, "Answer": None}

        with patch.object(checker, "fetch_public_json", side_effect=public_response):
            details = checker.lookup_domain_registry_and_dns("indexline.org")
        self.assertEqual(details["registration_rdap"], "RDAP_RECORD_OBSERVED")
        self.assertIsNone(details["rdap_expiry_event"])
        self.assertEqual(details["dns_ns"], "NO_MATCHING_ANSWERS_OBSERVED")
        self.assertEqual(details["dns_mx"], "NO_MATCHING_ANSWERS_OBSERVED")


    def test_nxdomain_response_does_not_prove_registrar_expiry(self):
        def public_response(url):
            if "rdap.publicinterestregistry.org/rdap/domain/" in url:
                return {"ldhName": "not-the-domain.example"}
            return {"Status": 3}

        with patch.object(checker, "fetch_public_json", side_effect=public_response):
            details = checker.lookup_domain_registry_and_dns("indexline.org")
        self.assertEqual(details["registration_rdap"], "RDAP_RESPONSE_IDENTITY_UNVERIFIED")
        self.assertEqual(details["dns_ns"], "NXDOMAIN_RESPONSE_NOT_REGISTRAR_PROOF")
        self.assertEqual(details["dns_mx"], "NXDOMAIN_RESPONSE_NOT_REGISTRAR_PROOF")


    def test_page_identity_rejects_footer_only_and_script_only_mentions(self):
        self.assertFalse(checker.has_index_line_page_identity(
            "<html><title>Unrelated page</title><footer>"
            "<a href='/theindexline/'>The Index Line</a></footer></html>"
        ))
        self.assertFalse(checker.has_index_line_page_identity(
            "<html><script>const x = 'The Index Line';</script></html>"
        ))
        self.assertTrue(checker.has_index_line_page_identity(
            "<html><h1>The <span>Index</span> Line</h1></html>"
        ))
        self.assertTrue(checker.has_index_line_page_identity(
            "<title>The&nbsp;Index Line - public archive</title>"
        ))

    def test_footer_marker_does_not_mark_unrelated_route_as_matching(self):
        url = "https://www.mcloughlin.world/theindexline/"
        unrelated = "<title>Page unavailable</title><footer>The Index Line</footer>"
        with (
            patch.object(checker.socket, "getaddrinfo", return_value=[("ok",)]),
            patch.object(checker, "fetch_text", return_value=(200, url, unrelated)),
        ):
            row = checker.observe_related_public_surfaces((("historic_route", url),))[0]
        self.assertEqual(row["http_observation"], "RESPONSE_NOT_SUFFICIENT_FOR_ROUTE_MATCH")
        self.assertEqual(row["editorial_approval"], "NOT_VERIFIED")

    def test_related_only_diagnostic_has_no_ssa_check_or_approval(self):
        expected = [{"surface_id": "historic_route", "http_observation": "UNKNOWN"}]
        buffer = io.StringIO()
        with (
            patch.object(checker, "observe_related_public_surfaces", return_value=expected),
            patch.object(
                checker, "verify_hosted_release_artifacts",
                side_effect=AssertionError("SSA release must not run in diagnostic mode")
            ),
            redirect_stdout(buffer),
        ):
            checker.show_related_index_line_observations()
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["observations"], expected)
        self.assertEqual(payload["purpose"], "read_only_index_line_public_surface_diagnostics")
        self.assertIn("UNKNOWN != PASS", payload["claim_boundary"])
        self.assertNotIn("editorial_approved", payload)


    def test_main_writes_index_line_observations_into_existing_actions_receipt(self):
        """The scheduled main path must not require a manual copy from CI logs."""
        base = {
            "object_type": "ssa_hosted_artifact_integrity_receipt",
            "status": "PARTIAL_VERIFIED",
            "summary": {
                "hosted_artifacts_retrieved": 2,
                "declared_artifacts": 2,
                "exact_repository_matches": 1,
                "exact_repository_comparisons": 1,
                "acknowledged_repository_mismatches": 0,
                "package_member_matches": 0,
                "package_member_comparisons": 0,
            },
        }
        observed = [{
            "surface_id": "indexline_org_unverified_domain",
            "address_resolution": "LOOKUP_FAILED_NOT_PROOF_OF_EXPIRY",
            "http_observation": "FETCH_FAILED_NOT_PROOF_OF_DOMAIN_STATUS",
            "registration": "UNKNOWN",
            "oncord_connection": "UNKNOWN",
            "editorial_approval": "NOT_VERIFIED",
            "publication_authorisation": "NOT_VERIFIED",
        }]
        with TemporaryDirectory() as tmp:
            destination = Path(tmp) / "hosted-artifact-integrity-runtime.json"
            with (
                patch.object(checker, "ROOT", Path(tmp)),
                patch.object(checker, "PAGES", []),
                patch.object(checker, "INTEGRITY_RECEIPT", destination),
                patch.object(checker, "verify_hosted_release_artifacts", return_value=([], base)),
                patch.object(checker, "observe_related_public_surfaces", return_value=observed),
                patch.dict(checker.os.environ, {
                    "GITHUB_SHA": "a" * 40, "GITHUB_RUN_ID": "42501401002",
                }),
                redirect_stdout(io.StringIO()),
            ):
                checker.main()
            receipt = json.loads(destination.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "PARTIAL_VERIFIED")
        self.assertEqual(receipt["object_type"], "ssa_hosted_artifact_integrity_receipt")
        related = receipt["related_index_line_observations"]
        self.assertEqual(related["source_revision"], "a" * 40)
        self.assertEqual(related["run_id"], "42501401002")
        self.assertEqual(related["source"], "docs/website/OTHER-PUBLIC-SURFACES.md")
        self.assertEqual(related["observations"], observed)
        self.assertIn("UNKNOWN != PASS", related["claim_boundary"])
        self.assertEqual(related["observations"][0]["publication_authorisation"], "NOT_VERIFIED")

    def test_main_preserves_ssa_failure_and_marks_invalid_run_provenance_unknown(self):
        """Independent public observations must not turn release drift into PASS."""
        base = {
            "object_type": "ssa_hosted_artifact_integrity_receipt",
            "status": "FAIL",
            "summary": {
                "hosted_artifacts_retrieved": 0,
                "declared_artifacts": 1,
                "exact_repository_matches": 0,
                "exact_repository_comparisons": 0,
                "acknowledged_repository_mismatches": 0,
                "package_member_matches": 0,
                "package_member_comparisons": 0,
            },
        }
        with TemporaryDirectory() as tmp:
            destination = Path(tmp) / "hosted-artifact-integrity-runtime.json"
            with (
                patch.object(checker, "ROOT", Path(tmp)),
                patch.object(checker, "PAGES", []),
                patch.object(checker, "INTEGRITY_RECEIPT", destination),
                patch.object(checker, "verify_hosted_release_artifacts", return_value=(["fixture release drift"], base)),
                patch.object(checker, "observe_related_public_surfaces", return_value=[]),
                patch.dict(checker.os.environ, {
                    "GITHUB_SHA": "unverified", "GITHUB_RUN_ID": "not-a-run",
                }),
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()),
            ):
                with self.assertRaises(SystemExit) as exit_result:
                    checker.main()
            receipt = json.loads(destination.read_text(encoding="utf-8"))
        self.assertEqual(exit_result.exception.code, 1)
        self.assertEqual(receipt["status"], "FAIL")
        self.assertIsNone(receipt["related_index_line_observations"]["source_revision"])
        self.assertIsNone(receipt["related_index_line_observations"]["run_id"])
        self.assertEqual(receipt["related_index_line_observations"]["observations"], [])


    def test_ssa_manifest_failure_still_emits_index_line_diagnostics_once(self):
        """Unrelated release failure must not suppress public diagnostic evidence."""
        observed = [{
            "surface_id": "indexline_org_unverified_domain",
            "address_resolution": "LOOKUP_FAILED_NOT_PROOF_OF_EXPIRY",
            "http_observation": "FETCH_FAILED_NOT_PROOF_OF_DOMAIN_STATUS",
            "editorial_approval": "NOT_VERIFIED",
            "publication_authorisation": "NOT_VERIFIED",
        }]
        with TemporaryDirectory() as tmp:
            destination = Path(tmp) / "hosted-artifact-integrity-runtime.json"
            summary_path = Path(tmp) / "summary.md"
            output, errors = io.StringIO(), io.StringIO()
            with (
                patch.object(checker, "ROOT", Path(tmp)),
                patch.object(checker, "PAGES", []),
                patch.object(checker, "INTEGRITY_RECEIPT", destination),
                patch.object(checker, "verify_hosted_release_artifacts",
                             return_value=(["canonical manifest unreadable"], {})),
                patch.object(checker, "observe_related_public_surfaces",
                             return_value=observed) as probe,
                patch.dict(checker.os.environ, {"GITHUB_STEP_SUMMARY": str(summary_path)}),
                redirect_stdout(output), redirect_stderr(errors),
            ):
                with self.assertRaises(SystemExit) as result:
                    checker.main()
            self.assertEqual(result.exception.code, 1)
            self.assertEqual(probe.call_count, 1)
            self.assertFalse(destination.exists())
            self.assertIn("indexline_org_unverified_domain", summary_path.read_text(encoding="utf-8"))
            self.assertIn("UNKNOWN != PASS", summary_path.read_text(encoding="utf-8"))
            self.assertIn("Index Line diagnostic indexline_org_unverified_domain", output.getvalue())
            self.assertIn("canonical manifest unreadable", errors.getvalue())

    def test_actions_summary_reuses_existing_review_surface_and_scrubs_untrusted_text(self):
        rows = [{
            "surface_id": "indexline_org_unverified_domain",
            "address_resolution": "LOOKUP_FAILED_NOT_PROOF_OF_EXPIRY",
            "http_observation": "FETCH_FAILED_NOT_PROOF_OF_DOMAIN_STATUS",
            "registration_rdap": "RDAP_LOOKUP_FAILED_NOT_PROOF_OF_EXPIRY",
            "dns_ns": "NXDOMAIN_RESPONSE_NOT_REGISTRAR_PROOF",
            "dns_mx": "NXDOMAIN_RESPONSE_NOT_REGISTRAR_PROOF",
            "oncord_connection": "UNKNOWN",
            "editorial_approval": "NOT_VERIFIED",
            "publication_authorisation": "<script>untrusted</script>",
        }]
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.md"
            path.write_text("Existing job evidence\n", encoding="utf-8")
            with patch.dict(checker.os.environ, {"GITHUB_STEP_SUMMARY": str(path)}):
                checker.append_index_line_actions_summary(rows)
            summary = path.read_text(encoding="utf-8")
        self.assertTrue(summary.startswith("Existing job evidence\n"))
        self.assertIn("indexline_org_unverified_domain", summary)
        self.assertIn("NXDOMAIN_RESPONSE_NOT_REGISTRAR_PROOF", summary)
        self.assertIn("NOT_VERIFIED | UNKNOWN |", summary)
        self.assertIn("UNKNOWN != PASS", summary)
        self.assertNotIn("<script>", summary)
        self.assertNotIn("registrant_email", summary)

    def test_pr_diagnostic_observes_once_and_writes_native_job_summary(self):
        observations = [{
            "surface_id": "historic_route",
            "http_observation": "HTTP_200_EXPECTED_MARKER_OBSERVED",
            "editorial_approval": "NOT_VERIFIED",
            "publication_authorisation": "NOT_VERIFIED",
        }]
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.md"
            output = io.StringIO()
            with (
                patch.object(checker, "observe_related_public_surfaces", return_value=observations) as probe,
                patch.dict(checker.os.environ, {"GITHUB_STEP_SUMMARY": str(path)}),
                redirect_stdout(output),
            ):
                checker.show_related_index_line_observations()
            summary = path.read_text(encoding="utf-8")
        self.assertEqual(probe.call_count, 1)
        self.assertEqual(json.loads(output.getvalue())["observations"], observations)
        self.assertIn("HTTP_200_EXPECTED_MARKER_OBSERVED", summary)
        self.assertIn("author rights", summary)
        self.assertIn("UNKNOWN != PASS", summary)



class ReceiptReadbackTests(unittest.TestCase):
    """Offline verification of the existing scheduled receipt, without new probes."""

    @staticmethod
    def sample_receipt():
        return {
            "object_type": "ssa_hosted_artifact_integrity_receipt",
            "status": "KNOWN_MISMATCH_STABLE",
            "related_index_line_observations": {
                "source": "docs/website/OTHER-PUBLIC-SURFACES.md",
                "source_revision": "a" * 40,
                "run_id": "42524656628",
                "observations": [
                    {
                        "surface_id": surface_id, "url": url,
                        "observed_at": "2026-11-08T21:20:00+00:00",
                        "oncord_connection": "UNKNOWN",
                        "editorial_approval": "NOT_VERIFIED",
                        "publication_authorisation": "NOT_VERIFIED",
                    }
                    for surface_id, url in checker.RELATED_INDEX_LINE_SURFACES
                ],
            },
        }

    def readback(self, receipt):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "hosted-artifact-integrity-runtime.json"
            path.write_text(json.dumps(receipt), encoding="utf-8")
            with patch.dict(checker.os.environ, {
                "GITHUB_SHA": "a" * 40, "GITHUB_RUN_ID": "42524656628",
            }):
                return checker.verify_index_line_receipt_readback(path)

    def test_valid_scheduled_receipt_reuses_existing_artifact_without_network(self):
        with patch.object(checker, "observe_related_public_surfaces",
                          side_effect=AssertionError("readback must not probe")):
            self.assertEqual(self.readback(self.sample_receipt()), [])

    def test_stale_or_misattributed_run_provenance_is_rejected(self):
        receipt = self.sample_receipt()
        receipt["related_index_line_observations"]["run_id"] = "42521669058"
        receipt["related_index_line_observations"]["source_revision"] = "b" * 40
        failures = self.readback(receipt)
        self.assertTrue(any("source revision" in failure for failure in failures))
        self.assertTrue(any("run ID" in failure for failure in failures))

    def test_missing_or_duplicate_target_cannot_be_reported_complete(self):
        receipt = self.sample_receipt()
        related = receipt["related_index_line_observations"]
        related["observations"] = [related["observations"][0], related["observations"][0]]
        failures = self.readback(receipt)
        self.assertTrue(any("duplicate identity" in failure for failure in failures))
        self.assertTrue(any("incomplete" in failure for failure in failures))

    def test_technical_receipt_cannot_fabricate_editorial_or_oncord_approval(self):
        receipt = self.sample_receipt()
        row = receipt["related_index_line_observations"]["observations"][0]
        row["oncord_connection"] = "VERIFIED"
        row["publication_authorisation"] = "APPROVED"
        failures = self.readback(receipt)
        self.assertTrue(any("protected authority boundary" in failure for failure in failures))

    def test_unreadable_receipt_fails_closed(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.json"
            self.assertTrue(checker.verify_index_line_receipt_readback(path))

    def test_retained_artifact_exact_byte_readback_uses_existing_workflow(self):
        """The upload must be read back from GitHub before the job can pass."""
        workflow = (checker.ROOT / ".github/workflows/check-live-publication.yml").read_text(
            encoding="utf-8"
        )
        upload = workflow.index("name: Retain machine-readable hosted artifact integrity receipt")
        download = workflow.index("name: Download retained Index Line receipt for exact artifact readback")
        compare = workflow.index("name: Verify retained Index Line receipt matches producing bytes")
        self.assertLess(upload, download)
        self.assertLess(download, compare)
        self.assertIn("actions/upload-artifact@v4", workflow[upload:download])
        self.assertIn("actions/download-artifact@v4", workflow[download:compare])
        self.assertIn("name: ssa-hosted-artifact-integrity-${{ github.run_id }}",
                      workflow[upload:compare])
        self.assertIn("path: ${{ runner.temp }}/index-line-retained-receipt",
                      workflow[download:compare])
        self.assertIn("cmp --silent docs/website/hosted-artifact-integrity-runtime.json",
                      workflow[compare:])
        self.assertIn("if: always() && github.event_name != 'pull_request'",
                      workflow[download:compare])
        self.assertIn("if: always() && github.event_name != 'pull_request'",
                      workflow[compare:])
        self.assertIn("exit 1", workflow[compare:])
        self.assertIn("sha256sum", workflow[compare:])
        self.assertIn("Retained artifact SHA-256", workflow[compare:])
        self.assertIn("BYTES_MATCH_PRODUCER", workflow[compare:])
        self.assertIn("GITHUB_STEP_SUMMARY", workflow[compare:])
        self.assertIn("--verify-index-line-receipt-file", workflow[compare:])
        self.assertLess(
            workflow.index("cmp --silent", compare),
            workflow.index("--verify-index-line-receipt-file", compare),
        )
        self.assertLess(
            workflow.index("--verify-index-line-receipt-file", compare),
            workflow.index("receipt_sha=", compare),
        )

    def test_downloaded_receipt_independently_checks_run_identity_and_permissions(self):
        """A byte-identical transport does not substitute for source-bound readback."""
        with TemporaryDirectory() as tmp:
            downloaded = Path(tmp) / "downloaded.json"
            receipt = self.sample_receipt()
            downloaded.write_text(json.dumps(receipt), encoding="utf-8")
            with (
                patch.dict(checker.os.environ, {
                    "GITHUB_SHA": "a" * 40, "GITHUB_RUN_ID": "42524656628",
                }),
                redirect_stdout(io.StringIO()),
            ):
                checker.run_index_line_receipt_readback(downloaded)
                receipt["related_index_line_observations"]["run_id"] = "999"
                downloaded.write_text(json.dumps(receipt), encoding="utf-8")
                with redirect_stderr(io.StringIO()) as errors:
                    with self.assertRaises(SystemExit) as failed:
                        checker.run_index_line_receipt_readback(downloaded)
                self.assertEqual(failed.exception.code, 1)
                self.assertIn("recorded run ID", errors.getvalue())
                receipt["related_index_line_observations"]["run_id"] = "42524656628"
                receipt["related_index_line_observations"]["observations"][0]["publication_authorisation"] = "APPROVED"
                downloaded.write_text(json.dumps(receipt), encoding="utf-8")
                with redirect_stderr(io.StringIO()) as errors:
                    with self.assertRaises(SystemExit) as failed:
                        checker.run_index_line_receipt_readback(downloaded)
                self.assertEqual(failed.exception.code, 1)
                self.assertIn("protected authority boundary", errors.getvalue())

    def test_retained_artifact_comparison_rejects_missing_or_altered_bytes(self):
        """Byte identity must fail closed even when JSON parses or has the same length."""
        with TemporaryDirectory() as tmp:
            producer = Path(tmp) / "produced.json"
            downloaded = Path(tmp) / "retained.json"
            producer.write_bytes(b'{"status":"NOT_VERIFIED"}')
            downloaded.write_bytes(producer.read_bytes())

            def compared():
                return subprocess.run(
                    ["cmp", "--silent", str(producer), str(downloaded)],
                    capture_output=True, check=False,
                ).returncode

            self.assertEqual(compared(), 0)
            downloaded.write_bytes(b'{"status":"YES_VERIFIED"}')
            self.assertNotEqual(compared(), 0)
            downloaded.unlink()
            self.assertNotEqual(compared(), 0)


if __name__ == "__main__":
    unittest.main()
