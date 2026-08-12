# 安全边界

ChatAuth 的首要目标是把 refresh-token-backed auth primitive 做成可测试、可审计、可复用的 ChatArch 内核。它不是 OpenAI/Codex 私有鉴权的替代品，也不尝试恢复或生成厂商 token。

## Token 输出规则

- refresh token 只写入 `admin grants issue --handoff-file` 指定的 handoff 文件。
- runtime refresh/access token 只写入 `token import-refresh` / `token refresh` 指定的 token-store 文件。
- CLI JSON 输出和 Python API 返回值只包含元数据，不包含 token 明文。
- `token status` 只报告存在性、schema、过期时间等安全摘要。

## 文件权限与路径

`0.1.1` 已覆盖这些安全行为：

| 文件 | 权限/保护 |
| --- | --- |
| state directory | 尽量设置为 `0700` |
| SQLite DB | 尽量设置为 `0600` |
| signing key | `0600`，拒绝 symlink 目标 |
| handoff file | `0600` |
| token-store | `0600`，使用安全临时文件写入并避免覆盖 symlink |

如果 token-store 写失败，数据库中的 refresh rotation 会回滚，避免 DB 已旋转但机器侧 token-store 仍旧的半失败状态。

## 资源侧验证

资源服务不应该持有 issuer private key。推荐形态是：

1. issuer 导出 public JWKS；
2. resource service 读取 JWKS；
3. resource service 用 `verify_access_token(...)` 或等价逻辑校验：
   - signature；
   - `iss`；
   - `aud`；
   - required scopes；
   - `exp` / `iat` 时间窗口。

## 当前非目标

- 不实现真实 HTTP `/oauth/token` 服务；`chatauth service run` 在 `0.1.x` 中非零退出。
- 不实现 Authorization Code / PKCE login UI。
- 不读取或操作 CRS production、Redis、Nginx 或 OpenAI/Codex 真实凭据。
- 不假扮 `auth.openai.com`。

## 后续设计约束

未来加入 ASGI/HTTP 服务时，需要补充：

- endpoint 认证与 constant-time token 比较；
- request/response secret redaction；
- remote admin API 权限模型；
- key rotation 与 JWKS cache 语义；
- ChatEnv `ChatAuth` namespace 的单一 profile/provider 规则；
- HTTP smoke、negative auth tests、docs/quickstart 同步更新。
