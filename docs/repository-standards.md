# 测试与仓库规范

这一页记录 ChatAuth 当前应满足的 ChatArch 仓库规范，方便后续 PR/release review 直接对照。

## 包与仓库坐标

| 项 | 当前值 |
| --- | --- |
| GitHub repository | `ChatArch/ChatAuth` |
| Python distribution | `ChatAuth` |
| import module | `chatauth` |
| CLI command | `chatauth` |
| docs URL | `https://arch.gh.wzhecnu.cn/ChatAuth/` |
| Python floor | `>=3.10` |
| CLI tree runtime | `chatstyle>=0.2.0,<0.3.0` |
| 默认本地状态根 | `~/.chatarch/chatauth/` |

`0.1.x` 尚未注册 ChatEnv provider；未来加入 profile/config/token-store 集成时，必须使用单一 `ChatAuth` namespace，避免同时出现多个配置目录或隐式 fallback。

## 本地验证命令

```bash
python -m pip install -e '.[dev,docs]'
python -m pytest -q
mkdocs build --strict
python -m build
python -m twine check --strict dist/*
chatauth --version
chatauth --tree
chatauth --tree-brief
```

当前测试覆盖：

| 文件 | 覆盖点 |
| --- | --- |
| `tests/test_cli_contract.py` | version、ChatStyle full/brief CLI tree、`service run` 非零、写命令 dry-run |
| `tests/test_auth_flow.py` | init/client/subject/grant/import/refresh/JWKS/verify 全闭环 |
| `tests/test_security_regressions.py` | JWKS-only verify、audience/scope enforcement、私有文件权限、symlink 防护、DB/token-store rollback |
| `tests/test_docs_contract.py` | 文档 full/brief CLI tree 与真实 registry 对齐、ChatStyle/docs extras/URL/CI gate |
| `tests/test_version.py` | package version readback |

## Workflow 规范

| Workflow | 触发 | 作用 |
| --- | --- | --- |
| `CI` | push / PR to `main` | Python 3.10/3.11/3.12 测试、`--version`/full/brief tree smoke、MkDocs strict build |
| `Preview Docs` | PR to `main` | 构建 PR 文档预览并评论 `https://arch.gh.wzhecnu.cn/ChatAuth/dev/` |
| `Deploy Docs` | push to `main` | 发布正式文档到 `gh-pages:/` |
| `Publish` | `v*` tag | OIDC Trusted Publishing 到 PyPI |

发布要求：merge 不是 release。真实 `0.1.x+` release 必须在用户明确要求后，tag merged default-branch commit，通过 GitHub Actions + PyPI Trusted Publisher 发布，并完成 PyPI JSON/simple/clean install 回读。

## 文档规范

- 默认中文文档，`.en.md` 为英文镜像。
- 首页是导航 hub，不写成线性开发记录。
- full/brief CLI 树必须来自真实 `chatauth --tree` / `--tree-brief`，并由测试防 drift。
- Quickstart 必须跑通本地闭环，不能依赖真实 CRS/OpenAI/Codex 凭据。
- public docs 不写私有路径、主机、Feishu/Lark ID、token mask 或 workspace 内部记录。

## Git 与产物规范

- 默认通过 feature branch + PR 修改 `main`。
- `dist/`、`site/`、`*.egg-info/`、`__pycache__/`、`.pytest_cache/` 必须保持 ignored，不能提交生成产物。
- default branch 应启用 ChatArch 保护基线：需要 PR、review count 0、enforce admins、禁 force-push/delete。
- 每次合并/发布后，local checkout 应回到 clean `main` 并同步 `origin/main` 与 tags。
