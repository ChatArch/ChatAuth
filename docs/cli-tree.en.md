# CLI Tree

The tree below comes from the current `chatauth --tree` implementation. Tests compare this fenced block with `chatauth.cli.TREE` so README/docs cannot drift away from the real command surface.

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
│   ├── clients  # OAuth client registry.
│   │   ├── list  # List safe client metadata.
│   │   └── create  # Create a client; writes only with --execute.
│   ├── subjects  # Principals that can receive refresh grants.
│   │   ├── list  # List safe subject metadata.
│   │   └── create  # Create a subject; writes only with --execute.
│   ├── grants  # Refresh-token grant families.
│   │   ├── list  # List safe grant metadata.
│   │   └── issue  # Issue initial refresh token to a 0600 handoff file; writes only with --execute.
│   └── keys  # Signing keys and JWKS.
│       ├── list  # List signing-key metadata.
│       └── jwks  # Export public JWKS.
├── token  # Machine-side runtime token store operations.
│   ├── import-refresh  # Import refresh token from a handoff file; writes only with --execute.
│   ├── status  # Show token-store metadata without token values.
│   ├── refresh  # Exchange stored refresh token for access token and rotated refresh token; writes only with --execute.
│   └── clear  # Remove local runtime token store; writes only with --execute.
└── verify  # Resource-side verification helpers.
    ├── jwks  # Export public JWKS.
    └── access-token  # Verify stored access token audience/scope from local state or JWKS.
```

## Command groups

| Group | Responsibility | Mutation boundary |
| --- | --- | --- |
| `health` | quick state health readback | read-only |
| `service` | local issuer state lifecycle | `init` requires `--execute`; `run` is reserved and exits non-zero |
| `admin clients` | OAuth client registry | `create` requires `--execute` |
| `admin subjects` | subjects that can receive refresh grants | `create` requires `--execute` |
| `admin grants` | refresh-token grant family | `issue` requires `--execute` and writes a handoff file |
| `admin keys` | signing-key metadata / JWKS | read-only |
| `token` | machine-side runtime token-store | import / refresh / clear require `--execute` |
| `verify` | resource-side JWKS and access-token verification | read-only |

## Interfaces not implemented yet

`chatauth service run` is reserved and exits non-zero in `0.1.x`. It does not start an HTTP service and does not pretend the service is running. When a real ASGI/HTTP `/oauth/token` service is added, it should land with Python APIs, tests, quickstart updates, and deployment docs.
