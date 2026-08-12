# CLI 树

下面的树来自当前实现的 `chatauth --tree`。测试会比较此处的 fenced block 与 `chatauth.cli.TREE`，避免 README/docs 与真实命令面漂移。

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

## 命令分组

| 分组 | 职责 | 写入边界 |
| --- | --- | --- |
| `health` | 快速读取 state 健康状态 | 只读 |
| `service` | 本地 issuer state 生命周期 | `init` 需要 `--execute`；`run` 保留且非零退出 |
| `admin clients` | OAuth client registry | `create` 需要 `--execute` |
| `admin subjects` | 可接收 refresh grant 的主体 | `create` 需要 `--execute` |
| `admin grants` | refresh-token grant family | `issue` 需要 `--execute` 并写 handoff 文件 |
| `admin keys` | signing key metadata / JWKS | 只读 |
| `token` | 机器侧 runtime token-store | import / refresh / clear 需要 `--execute` |
| `verify` | 资源侧 JWKS 与 access token 校验 | 只读 |

## 当前未实现的接口

`chatauth service run` 是保留命令，在 `0.1.x` 中非零退出。它不会启动 HTTP 服务，也不会假装服务已运行。未来真正加入 ASGI/HTTP `/oauth/token` 服务时，应同时补充 Python API、测试、quickstart 和部署文档。
