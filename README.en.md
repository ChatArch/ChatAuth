# ChatAuth

ChatAuth is ChatArch's self-hosted OAuth-style refresh-token auth service kernel. It extracts the reusable pattern confirmed during CRS / ChatCRS work: a machine or service holds a refresh token, exchanges it with a ChatAuth issuer for a short-lived access token, and resource services verify that access token with public JWKS, issuer, audience, and scope checks.

ChatAuth does **not** imitate `auth.openai.com`, bypass vendor auth, or generate vendor-private tokens. It only implements a controlled auth primitive for ChatArch-owned service boundaries.

- Documentation: <https://arch.gh.wzhecnu.cn/ChatAuth/en/>
- Chinese README: [README.md](README.md)
- Source repository: <https://github.com/ChatArch/ChatAuth>

## Install

```bash
python -m pip install ChatAuth
chatauth --version
chatauth --tree
chatauth --tree-brief
```

## Quickstart

The smoke flow below writes only local example state, a handoff file, and a runtime token-store. All commands that mutate state require `--execute`; without it they return a plan only.

```bash
STATE=./.chatauth-state
STORE=./.runtime-token.json
HANDOFF=./.refresh-token.txt
JWKS=./.jwks.json

chatauth service init --state-dir "$STATE" --issuer https://auth.example.test --execute
chatauth service doctor --state-dir "$STATE"

chatauth admin clients create demo \
  --state-dir "$STATE" \
  --audience chatarch.internal \
  --scope agent:run \
  --execute

chatauth admin subjects create machine:demo --state-dir "$STATE" --execute

CLIENT_ID=$(chatauth admin clients list --state-dir "$STATE" \
  | python -c 'import json,sys; print(json.load(sys.stdin)["clients"][0]["client_id"])')

chatauth admin grants issue "$CLIENT_ID" machine:demo \
  --state-dir "$STATE" \
  --audience chatarch.internal \
  --scope agent:run \
  --handoff-file "$HANDOFF" \
  --execute

chatauth token import-refresh \
  --state-dir "$STATE" \
  --token-store "$STORE" \
  --from-file "$HANDOFF" \
  --execute

chatauth token refresh --state-dir "$STATE" --token-store "$STORE" --execute
chatauth admin keys jwks --state-dir "$STATE" > "$JWKS"

chatauth verify access-token \
  --token-store "$STORE" \
  --jwks-file "$JWKS" \
  --issuer https://auth.example.test \
  --audience chatarch.internal \
  --scope agent:run
```

Expected final output:

```text
valid
```

Security contract: CLI output reports only metadata such as booleans, paths, IDs, counts, and expiry times. Refresh tokens and access tokens are written only to explicit handoff/token-store files and are not printed by default.

## Current capabilities

Implemented in `0.1.x`:

- local SQLite state initialization, doctor, and health;
- RSA signing-key generation and JWKS export;
- client, subject, refresh-grant creation and safe listing;
- hashed refresh-token storage, single-use rotation, and short-lived RS256 access-token issuing;
- runtime token-store import / status / refresh / clear;
- resource-side access-token verification from public JWKS without issuer private-key access;
- private file permissions and symlink rejection for sensitive state, handoff, and token-store writes;
- `service run` is reserved and exits non-zero in `0.1.x` so automation cannot mistake it for a running service.

## CLI tree

See [CLI Tree](https://arch.gh.wzhecnu.cn/ChatAuth/en/cli-tree/) for the complete command surface. `chatauth --tree` renders the real Click registry with argument and option signatures; `chatauth --tree-brief` renders the same nodes and descriptions without signatures. Tests run both entry points and keep their output aligned with the documentation.

## Development checks

See [DEVELOP.md](DEVELOP.md) for the complete development and release contract.

```bash
python -m pip install -e '.[dev,docs]'
python -m pytest -q
mkdocs build --strict
python -m build
python -m twine check --strict dist/*
```
