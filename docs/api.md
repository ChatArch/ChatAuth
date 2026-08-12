# Python API

ChatAuth 的 CLI 是 `chatauth.operations` 上的薄适配层。其他 ChatArch 包不应该 shell out 到 `chatauth`，而应直接调用这些 importable functions，并让 CLI 只负责参数解析与输出格式。

## CLI 到 Python function 映射

| CLI | Python API | 说明 |
| --- | --- | --- |
| `chatauth health` | `doctor(...)` | 读取 state 健康摘要 |
| `chatauth service init` | `init_service(...)` | 初始化 state DB、issuer metadata、signing key |
| `chatauth service doctor` | `doctor(...)` | 读取 state/config/key metadata |
| `chatauth admin clients list` | `list_clients(...)` | 列出 client 安全 metadata |
| `chatauth admin clients create` | `create_client(...)` | 创建 client；`execute=False` 为 dry-run |
| `chatauth admin subjects list` | `list_subjects(...)` | 列出 subject 安全 metadata |
| `chatauth admin subjects create` | `create_subject(...)` | 创建 subject；`execute=False` 为 dry-run |
| `chatauth admin grants list` | `list_grants(...)` | 列出 grant family 安全 metadata |
| `chatauth admin grants issue` | `issue_refresh_grant(...)` | 创建 refresh grant 并写 handoff 文件；不返回 token 明文 |
| `chatauth admin keys list` | `list_keys(...)` | 列出 signing key metadata |
| `chatauth admin keys jwks` | `export_jwks(...)` | 导出公开 JWKS |
| `chatauth token import-refresh` | `import_refresh_token(...)` | 从 handoff 文件导入 refresh token 到 runtime token-store |
| `chatauth token status` | `token_status(...)` | 读取 token-store metadata；不返回 token 明文 |
| `chatauth token refresh` | `refresh_access_token(...)` | refresh grant rotation + access token 签发 |
| `chatauth token clear` | `clear_token_store(...)` | 删除显式 token-store |
| `chatauth verify jwks` | `export_jwks(...)` | 资源侧可用的 JWKS 导出 |
| `chatauth verify access-token` | `verify_access_token(...)` | 校验 access token issuer/audience/scope/signature |

## API 使用示例

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

## 返回值约定

- 写操作在 `execute=False` 时返回 `planned: true`，不产生副作用。
- 任何 refresh token / access token 明文都不会出现在返回 dict 中。
- 输出面可以包含 path、ID、issuer、audience、scope、过期时间、布尔状态和计数。
- `verify_access_token(...)` 可以用 `jwks` + `issuer` 在没有 issuer private key 的资源服务进程中运行。
