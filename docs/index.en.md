# ChatAuth

ChatAuth is ChatArch's self-hosted OAuth-style refresh-token auth service kernel. It separates refresh tokens, short-lived access tokens, public JWKS verification, audience/scope contracts, and local secure state management into an independent package instead of embedding that boundary in ChatCRS.

<div class="grid cards" markdown>

-   **Quickstart**

    ---

    Initialize local state, create a client / subject / grant, refresh a token, and verify it with JWKS.

    [Start here](quickstart.md)

-   **CLI Tree**

    ---

    Read the real `chatauth --tree` command surface and which commands mutate state.

    [View the CLI tree](cli-tree.md)

-   **Python API**

    ---

    The CLI is a thin adapter over `chatauth.operations`, so other ChatArch packages can reuse the core behavior.

    [View the API map](api.md)

-   **Security Boundaries**

    ---

    ChatAuth does not imitate OpenAI, does not print tokens, and does not require resource services to hold the issuer private key.

    [Review the boundaries](security.md)

</div>

## Current scope

`0.1.x` is a local issuer kernel:

| Capability | Status |
| --- | --- |
| SQLite state initialization / doctor | Implemented |
| RSA signing key / JWKS | Implemented |
| client / subject / refresh grant | Implemented |
| refresh-token hashing and rotation | Implemented |
| short-lived RS256 access tokens | Implemented |
| public-JWKS resource verification | Implemented |
| ASGI/HTTP `/oauth/token` service | Not implemented; `service run` exits non-zero |
| Authorization Code / PKCE UI | Not implemented |
| ChatEnv provider/profile integration | Not implemented; future work should use the `ChatAuth` namespace |

## Why this is not a ChatCRS subcommand

ChatCRS owns CRS Admin and Codex inspection surfaces. ChatAuth owns the reusable refresh-token-backed issuer primitive. Keeping ChatAuth independent lets ChatCRS, relays, agent runners, or other resource services consume the same auth boundary without coupling authorization to one business CLI.
