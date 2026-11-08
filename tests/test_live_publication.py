"""Offline regression tests for the existing live-publication checker.

Only read-only public route observations are covered. These tests never
authorise editorial release or classify domain renewal from DNS/HTTP.
"""

import io
import json
import socket
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
            if "rdap.org" in url:
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
            if "rdap.org" in url:
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
            if "rdap.org" in url:
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
            "registration": "UNKNOWN",
            "oncord_connection": "UNKNOWN",
            "editorial_approval": "NOT_VERIFIED",
            "publication_authorisation": "NOT_VERIFIED",
        }]
        with TemporaryDirectory() as tmp:
            destination = Path(tmp) / "hosted-artifact-integrity-runtime.json"
            with (
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


if __name__ == "__main__":
    unittest.main()
