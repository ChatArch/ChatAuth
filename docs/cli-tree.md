# CLI 树

下面两棵树都由 ChatStyle 从真实 Click command registry 生成。测试会直接运行 `chatauth --tree` 与 `chatauth --tree-brief` 并比较 fenced blocks，避免文档与真实命令面漂移。

## 完整树

`chatauth --tree` 保留参数与选项签名：

```text
chatauth
├── --help  # Show this message and exit.
├── --version  # Show the version and exit.
├── --tree  # Print the registered CLI tree and exit.
├── --tree-brief  # Print the registered CLI tree without parameter signatures and exit.
├── admin  # Local admin operations.
│   ├── clients  # OAuth client registry.
│   │   ├── create <NAME> [--state-dir STATE-DIR] [--audience AUDIENCE] [--scope SCOPES] [--execute]  # Plan an OAuth client; --execute writes it to local state.
│   │   └── list [--state-dir STATE-DIR]  # List safe OAuth client metadata without credentials.
│   ├── grants  # Refresh-token grant families.
│   │   ├── issue <CLIENT-ID> <SUBJECT> [--state-dir STATE-DIR] [--audience AUDIENCE] [--scope SCOPES] [--ttl-days TTL-DAYS] [--handoff-file HANDOFF-FILE] [--execute]  # Plan a refresh grant; --execute writes state and a private handoff file.
│   │   └── list [--state-dir STATE-DIR]  # List safe refresh-grant metadata without token values.
│   ├── keys  # Signing keys and JWKS.
│   │   ├── jwks [--state-dir STATE-DIR]  # Export public JWKS without private key material.
│   │   └── list [--state-dir STATE-DIR]  # List signing-key metadata without private key material.
│   └── subjects  # Principals that can receive refresh grants.
│       ├── create <SUBJECT> [--state-dir STATE-DIR] [--display-name DISPLAY-NAME] [--execute]  # Plan a subject; --execute writes it to local state.
│       └── list [--state-dir STATE-DIR]  # List safe subject metadata without credentials.
├── health [--state-dir STATE-DIR]  # Check local ChatAuth state health without changing it.
├── service  # Local ChatAuth service lifecycle.
│   ├── doctor [--state-dir STATE-DIR]  # Inspect local state, config, and key metadata without secrets.
│   ├── init [--state-dir STATE-DIR] [--issuer ISSUER] [--execute]  # Plan local state setup; --execute creates the database and signing key.
│   └── run  # Reserved ASGI service runner; exits non-zero in ChatAuth 0.1.x.
├── token  # Machine-side runtime token store operations.
│   ├── clear [--token-store TOKEN-STORE] [--execute]  # Plan token-store removal; --execute deletes the local store.
│   ├── import-refresh [--state-dir STATE-DIR] [--token-store TOKEN-STORE] [--from-file FROM-FILE] [--execute]  # Plan refresh-token import; --execute writes the private token store.
│   ├── refresh [--state-dir STATE-DIR] [--token-store TOKEN-STORE] [--execute]  # Plan token rotation; --execute updates the private token store.
│   └── status [--token-store TOKEN-STORE]  # Show token-store metadata without token values.
└── verify  # Resource-side verification helpers.
    ├── access-token [--state-dir STATE-DIR] [--token-store TOKEN-STORE] [--audience AUDIENCE] [--scope SCOPES] [--jwks-file JWKS-FILE] [--issuer ISSUER]  # Verify the stored access token and print only valid or invalid.
    └── jwks [--state-dir STATE-DIR]  # Export public JWKS for resource-side verification.
```

## 简洁树

`chatauth --tree-brief` 保留相同节点与说明，但省略参数和选项签名：

```text
chatauth
├── --help  # Show this message and exit.
├── --version  # Show the version and exit.
├── --tree  # Print the registered CLI tree and exit.
├── --tree-brief  # Print the registered CLI tree without parameter signatures and exit.
├── admin  # Local admin operations.
│   ├── clients  # OAuth client registry.
│   │   ├── create  # Plan an OAuth client; --execute writes it to local state.
│   │   └── list  # List safe OAuth client metadata without credentials.
│   ├── grants  # Refresh-token grant families.
│   │   ├── issue  # Plan a refresh grant; --execute writes state and a private handoff file.
│   │   └── list  # List safe refresh-grant metadata without token values.
│   ├── keys  # Signing keys and JWKS.
│   │   ├── jwks  # Export public JWKS without private key material.
│   │   └── list  # List signing-key metadata without private key material.
│   └── subjects  # Principals that can receive refresh grants.
│       ├── create  # Plan a subject; --execute writes it to local state.
│       └── list  # List safe subject metadata without credentials.
├── health  # Check local ChatAuth state health without changing it.
├── service  # Local ChatAuth service lifecycle.
│   ├── doctor  # Inspect local state, config, and key metadata without secrets.
│   ├── init  # Plan local state setup; --execute creates the database and signing key.
│   └── run  # Reserved ASGI service runner; exits non-zero in ChatAuth 0.1.x.
├── token  # Machine-side runtime token store operations.
│   ├── clear  # Plan token-store removal; --execute deletes the local store.
│   ├── import-refresh  # Plan refresh-token import; --execute writes the private token store.
│   ├── refresh  # Plan token rotation; --execute updates the private token store.
│   └── status  # Show token-store metadata without token values.
└── verify  # Resource-side verification helpers.
    ├── access-token  # Verify the stored access token and print only valid or invalid.
    └── jwks  # Export public JWKS for resource-side verification.
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
