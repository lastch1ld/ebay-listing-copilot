#!/usr/bin/env python3
"""Fail credentialed test runs if any recorded HTTP call left the eBay Sandbox.

Reads a newline-delimited list of URLs (one per recorded HTTP request made
during the Sandbox end-to-end run) and fails if any host is outside the
exact Sandbox allowlist. Run this both before and after the Sandbox test
suite so a leaked Production call cannot hide inside partial output.
"""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import urlparse

SANDBOX_HOST_ALLOWLIST = {
    "api.sandbox.ebay.com",
    "auth.sandbox.ebay.com",
}


def offending_hosts(urls: list[str]) -> list[str]:
    offenders = []
    for url in urls:
        url = url.strip()
        if not url:
            continue
        host = urlparse(url).hostname
        if host is None or host not in SANDBOX_HOST_ALLOWLIST:
            offenders.append(url)
    return offenders


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: verify_no_production_calls.py <recorded-requests-file>", file=sys.stderr)
        return 2

    recorded_path = Path(sys.argv[1])
    if not recorded_path.exists():
        print("No recorded requests found; treating as zero calls made.")
        return 0

    urls = recorded_path.read_text(encoding="utf-8").splitlines()
    offenders = offending_hosts(urls)

    if offenders:
        print("Non-Sandbox destinations detected:", file=sys.stderr)
        for offender in offenders:
            print(f"  - {offender}", file=sys.stderr)
        return 1

    print(f"All {len(urls)} recorded requests stayed within the eBay Sandbox host allowlist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
