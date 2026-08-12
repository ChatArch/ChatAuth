# ChatAuth

ChatAuth 是 ChatArch 自托管的 OAuth-style refresh-token 鉴权服务内核。它把最近 CRS / ChatCRS 讨论里确认的通用模式抽出来：机器或服务持有 refresh token，向 ChatAuth issuer 换取短期 access token；资源服务只需要用公开 JWKS 校验 access token 的 issuer、audience 和 scope。

ChatAuth **不**复刻、假扮或绕过 `auth.openai.com`，也不生成任何厂商私有 token。它只提供 ChatArch 自有服务边界内可控的 refresh-token-backed auth primitive。

- 文档站：<https://arch.gh.wzhecnu.cn/ChatAuth/>
- English README: [README.en.md](README.en.md)
- 源码仓库：<https://github.com/ChatArch/ChatAuth>

## 安装

```bash
python -m pip install ChatAuth
chatauth --version
chatauth --tree
```

## 快速开始

下面的 smoke flow 只在当前目录写入示例状态、handoff 文件和 runtime token-store；所有会写状态的命令都必须带 `--execute`，否则只返回计划结果。

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

期望最后一行输出：

```text
valid
```

安全约定：CLI 默认只输出布尔值、路径、ID、计数和过期时间等元数据；refresh token / access token 只写入显式指定的 handoff/token-store 文件，不会直接打印。

## 当前能力

`0.1.x` 已实现：

- 本地 SQLite state 初始化、doctor 与 health；
- RSA signing key 生成与 JWKS 导出；
- client、subject、refresh grant 创建和安全列表；
- refresh token 哈希存储、一次性 rotation 和短期 RS256 access token 签发；
- runtime token-store import / status / refresh / clear；
- 资源侧基于公开 JWKS 的 access token 校验，不需要 issuer private key；
- 敏感 state、handoff、token-store 文件使用私有权限并拒绝关键 symlink 写入；
- `service run` 在 `0.1.x` 中保留且非零退出，避免伪装成已运行服务。

## CLI 树

完整命令面见 [CLI 树](https://arch.gh.wzhecnu.cn/ChatAuth/cli-tree/)。源码测试会把文档中的 CLI tree 与真实 `chatauth --tree` 对齐。

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

## 开发验证

```bash
python -m pip install -e '.[dev,docs]'
python -m pytest -q
mkdocs build --strict
python -m build
python -m twine check --strict dist/*
```
