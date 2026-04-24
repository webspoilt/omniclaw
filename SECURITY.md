# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| v4.5.x  | ✅ Yes             |
| < v4.5  | ❌ No              |

## Reporting a Vulnerability

We take the security of OmniClaw very seriously. If you find a security vulnerability, please do **not** open a public issue.

Instead, please report vulnerabilities by:
1. Sending an email to **security@omniclaw.ai**
2. Providing a detailed description of the vulnerability, including steps to reproduce.
3. Attaching any relevant logs or screenshots.

We will acknowledge your report within 48 hours and provide a timeline for a fix.

## Security Hygiene
- **Secrets**: Never commit API keys to this repository.
- **Sandbox**: Always run autonomous agents in a sandboxed environment.
- **Audit**: All security-critical modules (ShellSandbox, FileGuard) are subject to peer review.
