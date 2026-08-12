# Changelog

## 0.1.1 - 2026-08-12

Security hotfix after late independent review of `0.1.0`:

- Add public-JWKS access-token verification so resource services do not need issuer private-key access.
- Enforce client audience and scope contracts before issuing refresh grants.
- Harden sensitive state, handoff, and token-store writes with private file modes, unique temp files, and symlink rejection for issuer private keys / DB paths.
- Keep refresh-token rotation and runtime token-store writes in one transaction boundary so DB state rolls back if the token-store write fails.

## 0.1.0 - 2026-08-12

First functional MVP release:

- Local ChatAuth state initialization and doctor.
- Client, subject, refresh grant, key/JWKS, token-store, refresh, and verification commands.
- Hashed refresh-token storage, refresh rotation, RS256 access tokens, JWKS export, and CLI dry-run defaults for writes.
