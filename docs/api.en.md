# Python API

The ChatAuth CLI is a thin adapter over `chatauth.operations`. Other ChatArch packages should call these importable functions directly instead of shelling out to `chatauth`; the CLI should only parse arguments and render output.

## CLI to Python function map

| CLI | Python API | Notes |
| --- | --- | --- |
| `chatauth health` | `doctor(...)` | read state health metadata |
| `chatauth service init` | `init_service(...)` | initialize state DB, issuer metadata, and signing key |
| `chatauth service doctor` | `doctor(...)` | read state/config/key metadata |
| `chatauth admin clients list` | `list_clients(...)` | list safe client metadata |
| `chatauth admin clients create` | `create_client(...)` | create a client; `execute=False` is dry-run |
| `chatauth admin subjects list` | `list_subjects(...)` | list safe subject metadata |
| `chatauth admin subjects create` | `create_subject(...)` | create a subject; `execute=False` is dry-run |
| `chatauth admin grants list` | `list_grants(...)` | list safe grant-family metadata |
| `chatauth admin grants issue` | `issue_refresh_grant(...)` | create a refresh grant and write a handoff file; never returns raw tokens |
| `chatauth admin keys list` | `list_keys(...)` | list signing-key metadata |
| `chatauth admin keys jwks` | `export_jwks(...)` | export public JWKS |
| `chatauth token import-refresh` | `import_refresh_token(...)` | import a refresh token from a handoff file into a runtime token-store |
| `chatauth token status` | `token_status(...)` | read token-store metadata; never returns token values |
| `chatauth token refresh` | `refresh_access_token(...)` | refresh-grant rotation plus access-token issuing |
| `chatauth token clear` | `clear_token_store(...)` | remove the explicit token-store |
| `chatauth verify jwks` | `export_jwks(...)` | JWKS export for resource services |
| `chatauth verify access-token` | `verify_access_token(...)` | verify issuer/audience/scope/signature |

## API example

```python
from pathlib import Path

from chatauth.operations import (
    create_client,
    create_subject,
    export_jwks,
    import_refresh_token,
    init_service,
    issue_refresh_grant,
    refresh_access_token,
    verify_access_token,
)

state_dir = Path(".chatauth-state")
token_store = Path(".runtime-token.json")
handoff = Path(".refresh-token.txt")

init_service(state_dir=state_dir, issuer="https://auth.example.test", execute=True)
client = create_client(
    state_dir=state_dir,
    name="demo",
    audience="chatarch.internal",
    scopes=["agent:run"],
    execute=True,
)
create_subject(state_dir=state_dir, subject="machine:demo", execute=True)
issue_refresh_grant(
    state_dir=state_dir,
    client_id=client["client_id"],
    subject="machine:demo",
    audience="chatarch.internal",
    scopes=["agent:run"],
    handoff_file=handoff,
    execute=True,
)
import_refresh_token(state_dir=state_dir, token_store=token_store, from_file=handoff, execute=True)
refresh_access_token(state_dir=state_dir, token_store=token_store, execute=True)
jwks = export_jwks(state_dir=state_dir)
result = verify_access_token(
    state_dir=None,
    token_store=token_store,
    jwks=jwks,
    issuer="https://auth.example.test",
    audience="chatarch.internal",
    scopes=["agent:run"],
)
assert result["valid"] is True
```

## Return-value contract

- Mutation operations return `planned: true` and have no side effects when `execute=False`.
- Raw refresh-token / access-token values never appear in returned dictionaries.
- Output may include paths, IDs, issuer, audience, scope, expiry times, boolean status, and counts.
- `verify_access_token(...)` can run in a resource-service process with only `jwks` + `issuer`, without issuer private-key access.
