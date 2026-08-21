# Changelog

## Unreleased

## 0.1.2 - 2026-08-21

- 将顶层 CLI tree 迁移到 `chatstyle>=0.2.0,<0.3.0` 的共享 Click runtime，移除手写 tree 常量。
- 新增 `chatauth --tree-brief`，保留真实注册命令与说明并省略参数签名。
- 显式固定公共根命令名为 `chatauth`，并为所有 group/leaf 补齐 side-effect 与敏感信息边界说明。
- CI 新增已安装 console script 的 `--tree-brief` 回读，测试同时校验 full/brief tree 与文档一致。
- 新增正式 MkDocs 文档站：中文默认页面 + 英文镜像页面。
- 扩展 README quickstart、CLI 树、Python API、安全边界、测试与仓库规范文档。
- 新增文档漂移测试，并让 CI 执行 `mkdocs build --strict`。

## 0.1.1 - 2026-08-12

`0.1.0` 发布后的独立安全复核补丁：

- 新增 public-JWKS access-token verification，资源服务无需持有 issuer private key。
- 在签发 refresh grant 前校验 client audience 与 scope contract。
- 强化敏感 state、handoff、token-store 写入：私有文件权限、唯一临时文件、issuer private key / DB 路径 symlink 拒绝。
- refresh-token rotation 与 runtime token-store 写入保持同一事务边界；token-store 写失败时 DB 状态回滚。

## 0.1.0 - 2026-08-12

首个可用 MVP release：

- 本地 ChatAuth state 初始化与 doctor。
- Client、subject、refresh grant、key/JWKS、token-store、refresh、verification 命令。
- Refresh-token hash 存储、refresh rotation、RS256 access token、JWKS export，以及 CLI 写操作默认 dry-run。
