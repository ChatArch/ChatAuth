# Security Boundaries

ChatAuth's primary goal is to make a refresh-token-backed auth primitive testable, auditable, and reusable inside ChatArch. It is not an OpenAI/Codex private-auth replacement and does not try to recover or generate vendor tokens.

## Token output rules

- Refresh tokens are written only to the handoff file passed to `admin grants issue --handoff-file`.
- Runtime refresh/access tokens are written only to the token-store file passed to `token import-refresh` / `token refresh`.
- CLI JSON output and Python API return values contain metadata only, never raw token values.
- `token status` reports safe summaries such as existence, schema, and expiry metadata.

## File permissions and paths

`0.1.1` covers these safety behaviors:

| File | Permission / protection |
| --- | --- |
| state directory | best-effort `0700` |
| SQLite DB | best-effort `0600` |
| signing key | `0600`, rejects symlink targets |
| handoff file | `0600` |
| token-store | `0600`, safe temp-file writes, avoids symlink overwrite |

If the token-store write fails, the database refresh rotation rolls back so the DB cannot rotate while the machine-side token-store remains stale.

## Resource-side verification

Resource services should not hold the issuer private key. Recommended shape:

1. the issuer exports public JWKS;
2. the resource service reads JWKS;
3. the resource service uses `verify_access_token(...)` or equivalent logic to check:
   - signature;
   - `iss`;
   - `aud`;
   - required scopes;
   - `exp` / `iat` time window.

## Current non-goals

- No real HTTP `/oauth/token` service yet; `chatauth service run` exits non-zero in `0.1.x`.
- No Authorization Code / PKCE login UI.
- No access to CRS production, Redis, Nginx, or real OpenAI/Codex credentials.
- No imitation of `auth.openai.com`.

## Future design constraints

When ASGI/HTTP service support is added, it should include:

- endpoint authentication and constant-time token comparison;
- request/response secret redaction;
- remote admin API authorization model;
- key rotation and JWKS cache semantics;
- a single ChatEnv `ChatAuth` namespace/provider rule;
- HTTP smoke tests, negative auth tests, and synchronized docs/quickstart updates.
