#!/usr/bin/env python3
"""Read-only checks against the live McLoughlin.world publication surface.

This script detects drift between repository expectations and the public site.
It never changes canonical content and should be treated as a monitoring aid,
not as publication authority.
"""

from __future__ import annotations

import sys
import urllib.error
import urllib.request

USER_AGENT = "McLoughlin.World-publication-check/1.0"
TIMEOUT = 20

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


def fetch_text(url: str) -> tuple[int, str, str]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        status = response.getcode()
        final_url = response.geturl()
        body = response.read().decode("utf-8", errors="replace")
        return status, final_url, body


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

    if failures:
        print("Live-publication drift check failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        raise SystemExit(1)

    print("Live-publication drift check passed.")


if __name__ == "__main__":
    main()
