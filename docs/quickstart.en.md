# Quickstart

This flow uses only local files. It does not need CRS, Redis, Nginx, or real OpenAI/Codex tokens. It verifies the minimum ChatAuth loop: issuer state → client → subject → refresh grant → runtime token-store → access token → JWKS verification.

## Install and read back the version {#install-verify}

```bash
python -m pip install ChatAuth
chatauth --version
chatauth --tree
chatauth --tree-brief
```

## Local smoke flow {#local-smoke}

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

The final command should print:

```text
valid
```

## Dry-run and mutation boundary {#dry-run-execute}

Mutation commands are dry-run by default. Add `--execute` for real writes:

| Command | Without `--execute` | With `--execute` |
| --- | --- | --- |
| `service init` | returns a plan and does not create state | creates the state DB and signing key |
| `admin clients create` | returns a plan and does not write a client | writes client metadata |
| `admin subjects create` | returns a plan and does not write a subject | writes subject metadata |
| `admin grants issue` | returns a plan and does not write a handoff | creates a refresh grant and writes the refresh token to a 0600 handoff file |
| `token import-refresh` | returns a plan and does not write a token-store | imports the refresh token from the handoff file |
| `token refresh` | returns a plan and does not rotate tokens | rotates the refresh token and writes a short-lived access token |
| `token clear` | returns a plan and does not remove the token-store | removes the explicit token-store file |

## Remove quickstart files {#cleanup}

```bash
rm -rf ./.chatauth-state ./.runtime-token.json ./.refresh-token.txt ./.jwks.json
```

In the Playground workspace, move project files to the nearest `.trash/` when cleaning repository/task artifacts. The command above is only for quickstart scratch files that the user created locally.
