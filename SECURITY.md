# Security Policy

## Supported versions

This is a single-branch reference project. Only the `main` branch is
supported; there are no maintained release branches or backports.

## Reporting a vulnerability

Please report suspected vulnerabilities privately instead of opening a public
issue:

1. Use GitHub's private vulnerability reporting for this repository
   (**Security** tab → **Report a vulnerability**).
2. Include what you found, how to reproduce it, and its potential impact.
3. Do not include real credentials, tokens, or personal data in your report —
   use redacted or fictional examples.

You will get an acknowledgement as soon as possible. Once a fix is available,
it will be released on `main` and noted in the commit history; this project
does not currently issue CVEs.

## Scope

In scope:

- The application code in `backend/` and `frontend/`.
- The GitHub Actions workflows in `.github/workflows/`.
- The credential-handling, redaction, and approval rules described in
  [`AGENTS.md`](AGENTS.md) and [`docs/privacy.md`](docs/privacy.md).

Out of scope:

- Vulnerabilities in eBay's, OpenAI's, or any shipping/tracking provider's own
  services — report those to the respective provider.
- Findings that require an attacker to already have your local machine or
  your `.env` file.

## Handling of confirmed issues

Confirmed credential exposure follows the incident-response steps in
[`AGENTS.md`](AGENTS.md#8-credential-incident-response): revoke first, then
clean up the repository and history, and add a regression test or scanner
rule to prevent recurrence.
