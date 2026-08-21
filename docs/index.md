# ChatAuth

ChatAuth 是 ChatArch 自托管的 OAuth-style refresh-token 鉴权服务内核。它把 refresh token、短期 access token、公开 JWKS 校验、audience/scope 合同和本地安全状态管理拆成一个独立包，而不是继续塞进 ChatCRS。

<div class="grid cards" markdown>

-   **快速开始**

    ---

    从本地 state 初始化开始，创建 client / subject / grant，完成 refresh 与 JWKS 验证闭环。

    [进入快速开始](quickstart.md)

-   **CLI 树**

    ---

    查看真实 `chatauth --tree` / `--tree-brief` 命令面，以及哪些命令会写状态、哪些命令只是读元数据。

    [查看 CLI 树](cli-tree.md)

-   **Python API**

    ---

    CLI 是薄适配层，核心行为位于 `chatauth.operations`，便于其他 ChatArch 包复用。

    [查看 API 映射](api.md)

-   **安全边界**

    ---

    明确 ChatAuth 不假扮 OpenAI、不打印 token、不让资源服务接触 issuer private key。

    [查看安全边界](security.md)

</div>

## 当前范围

`0.1.x` 是本地 issuer 内核：

| 能力 | 状态 |
| --- | --- |
| SQLite state 初始化 / doctor | 已实现 |
| RSA signing key / JWKS | 已实现 |
| client / subject / refresh grant | 已实现 |
| refresh token 哈希存储与 rotation | 已实现 |
| 短期 RS256 access token | 已实现 |
| 公开 JWKS 资源侧验证 | 已实现 |
| ASGI/HTTP `/oauth/token` 服务 | 未实现，`service run` 非零退出 |
| Authorization Code / PKCE UI | 未实现 |
| ChatEnv provider/profile 集成 | 未实现，后续应统一使用 `ChatAuth` namespace |

## 为什么不是 ChatCRS 的子命令

ChatCRS 负责 CRS Admin / Codex inspection 这类 CRS 边界内的操作；ChatAuth 负责可复用的 refresh-token-backed issuer primitive。把 ChatAuth 独立出来后，ChatCRS、未来的 relay、agent runner 或其他资源服务都可以作为 consumer，而不用把授权服务和某个业务 CLI 绑死。
