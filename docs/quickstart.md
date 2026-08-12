# 快速开始

这个流程只使用本地文件，不需要 CRS、Redis、Nginx 或真实 OpenAI/Codex token。它验证 ChatAuth 的最小闭环：issuer state → client → subject → refresh grant → runtime token-store → access token → JWKS 验证。

## 安装与版本回读 {#install-verify}

```bash
python -m pip install ChatAuth
chatauth --version
chatauth --tree
```

## 本地 smoke flow {#local-smoke}

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

最后一步应输出：

```text
valid
```

## dry-run 与写入边界 {#dry-run-execute}

写操作默认 dry-run。需要真实写入时显式加 `--execute`：

| 命令 | 无 `--execute` | 有 `--execute` |
| --- | --- | --- |
| `service init` | 返回计划，不创建 state | 创建 state DB 和 signing key |
| `admin clients create` | 返回计划，不写 client | 写入 client metadata |
| `admin subjects create` | 返回计划，不写 subject | 写入 subject metadata |
| `admin grants issue` | 返回计划，不写 handoff | 生成 refresh grant，并把 refresh token 写入 0600 handoff 文件 |
| `token import-refresh` | 返回计划，不写 token-store | 从 handoff 导入 refresh token |
| `token refresh` | 返回计划，不旋转 token | 旋转 refresh token 并写入短期 access token |
| `token clear` | 返回计划，不删除 token-store | 删除显式 token-store 文件 |

## 清理示例文件 {#cleanup}

```bash
rm -rf ./.chatauth-state ./.runtime-token.json ./.refresh-token.txt ./.jwks.json
```

注意：正式 workspace 里需要删除或改动项目文件时，按 workspace 规范优先移动到就近 `.trash/`；上面的 `rm -rf` 只适用于 quickstart 里用户自己创建的示例临时文件。
