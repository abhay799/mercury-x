# Security Policy

## Project scope

MERCURY X is experimental research and portfolio software, not a deployed production service. Its fail-closed contracts and privacy/authorization invariants are architecture features; they do not constitute an external security assessment, compliance certification, or hardened deployment.

## Reporting a vulnerability

Do not include exploit details, credentials, private endpoints, personal data, or other sensitive material in a public issue.

This repository does not currently publish a dedicated security email, bug bounty, security team, or response SLA. Use a private repository-owner contact or the hosting platform's private vulnerability-reporting feature if one is available. If no private mechanism is available, the project presently lacks a safe public intake channel; do not disclose sensitive details publicly merely to create a report.

For non-sensitive hardening issues that do not expose an active vulnerability, a normal issue may describe the affected component, expected invariant, and a sanitized reproduction.

## Useful report context

Include only non-sensitive information needed to reproduce the issue:

- affected commit and component;
- relevant phase or productization surface;
- expected and observed fail-closed behavior;
- minimal sanitized reproduction;
- potential impact and trust boundary;
- whether the behavior involves synthetic, simulated, static-demo, or real external state.

No response time, remediation deadline, reward, or disclosure date is promised. Production adopters must perform their own threat modeling, dependency review, secrets management, identity integration, supply-chain controls, and penetration testing.
