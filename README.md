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
chatauth --tree-brief
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

完整命令面见 [CLI 树](https://arch.gh.wzhecnu.cn/ChatAuth/cli-tree/)。`chatauth --tree` 从真实 Click registry 输出带参数签名的完整树；`chatauth --tree-brief` 输出相同节点与说明，但省略签名。源码测试会直接运行两个入口并与文档对齐。

```bash
chatauth --tree
chatauth --tree-brief
```

## 开发验证

完整开发与 release 约定见 [DEVELOP.md](DEVELOP.md)。

```bash
python -m pip install -e '.[dev,docs]'
python -m pytest -q
mkdocs build --strict
python -m build
python -m twine check --strict dist/*
```
