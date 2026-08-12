# ChatAuth

Self-hosted OAuth-style refresh-token auth service for ChatArch.

ChatAuth extracts the reusable idea from recent ChatCRS / CRS service discussions: a machine or service keeps a refresh token, exchanges it at an authorization service for a short-lived access token, and resource services verify that access token against the issuer's public key material.

ChatAuth does **not** imitate `auth.openai.com` or reproduce vendor-private token logic. It implements a small self-hosted issuer boundary for ChatArch-owned services.

## Install

```bash
python -m pip install ChatAuth
```

## Command tree

```text
chatauth  # Self-hosted OAuth-style refresh-token auth service for ChatArch.
├── --help  # Show help.
├── --version  # Show installed version.
├── --tree  # Print the registered CLI tree.
├── health  # Check local ChatAuth state health.
├── service  # Local ChatAuth service lifecycle.
│   ├── init  # Plan/create local state DB and signing key; writes only with --execute.
│   ├── run  # Reserved ASGI service runner; currently non-zero.
│   └── doctor  # Inspect local state/config/key metadata without secrets.
├── admin  # Local admin operations.
│   ├── clients
│   ├── subjects
│   ├── grants
│   └── keys
├── token
│   ├── import-refresh
│   ├── status
│   ├── refresh
│   └── clear
└── verify
    ├── jwks
    └── access-token
```

## Local smoke

```bash
STATE=./.chatauth-state
STORE=./.runtime-token.json
HANDOFF=./.refresh-token.txt

chatauth service init --state-dir "$STATE" --issuer https://auth.example.test --execute
chatauth admin clients create demo --state-dir "$STATE" --audience chatarch.internal --scope agent:run --execute
chatauth admin subjects create machine:demo --state-dir "$STATE" --execute
CLIENT_ID=$(chatauth admin clients list --state-dir "$STATE" | python -c 'import json,sys; print(json.load(sys.stdin)["clients"][0]["client_id"])')
chatauth admin grants issue "$CLIENT_ID" machine:demo --state-dir "$STATE" --audience chatarch.internal --scope agent:run --handoff-file "$HANDOFF" --execute
chatauth token import-refresh --state-dir "$STATE" --token-store "$STORE" --from-file "$HANDOFF" --execute
chatauth token refresh --state-dir "$STATE" --token-store "$STORE" --execute
chatauth admin keys jwks --state-dir "$STATE" > ./.jwks.json
chatauth verify access-token --token-store "$STORE" --jwks-file ./.jwks.json --issuer https://auth.example.test --audience chatarch.internal --scope agent:run
```

CLI output intentionally reports booleans and metadata only. Raw refresh tokens are written only to explicit handoff/token-store files and are never printed by default.

## Current scope

Implemented in `0.1.x`:

- local SQLite state initialization and doctor;
- local RSA signing key generation and JWKS export;
- admin client/subject/refresh-grant creation;
- refresh-token hashing and rotation;
- client audience/scope enforcement when issuing refresh grants;
- short-lived RS256 access-token issuing;
- local runtime token-store import/refresh/status/clear;
- resource-side JWT/audience/scope verification from public JWKS without issuer private-key access.

Reserved for future versions:

- ASGI/HTTP `/oauth/token` server (`chatauth service run` exits non-zero for now);
- full authorization-code / PKCE login UI;
- remote admin API and multi-key rotation workflows.
