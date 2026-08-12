# Tests and Repository Standards

This page records the current ChatArch repository standards for ChatAuth so future PR/release reviews can check the same contract.

## Package and repository coordinates

| Item | Current value |
| --- | --- |
| GitHub repository | `ChatArch/ChatAuth` |
| Python distribution | `ChatAuth` |
| import module | `chatauth` |
| CLI command | `chatauth` |
| docs URL | `https://arch.gh.wzhecnu.cn/ChatAuth/` |
| Python floor | `>=3.10` |
| default local state root | `~/.chatarch/chatauth/` |

`0.1.x` does not register a ChatEnv provider yet. When profile/config/token-store integration is added, it must use one canonical `ChatAuth` namespace instead of multiple config directories or hidden fallback paths.

## Local verification commands

```bash
python -m pip install -e '.[dev,docs]'
python -m pytest -q
mkdocs build --strict
python -m build
python -m twine check --strict dist/*
```

Current test coverage:

| File | Coverage |
| --- | --- |
| `tests/test_cli_contract.py` | CLI tree, non-zero `service run`, dry-run mutation commands |
| `tests/test_auth_flow.py` | init/client/subject/grant/import/refresh/JWKS/verify full loop |
| `tests/test_security_regressions.py` | JWKS-only verify, audience/scope enforcement, private file permissions, symlink protection, DB/token-store rollback |
| `tests/test_docs_contract.py` | documented CLI tree aligned to real tree, docs extras/URL/CI docs build gate |
| `tests/test_version.py` | package version readback |

## Workflow standards

| Workflow | Trigger | Purpose |
| --- | --- | --- |
| `CI` | push / PR to `main` | Python 3.10/3.11/3.12 tests, CLI smoke, MkDocs strict build |
| `Preview Docs` | PR to `main` | build PR docs preview and comment `https://arch.gh.wzhecnu.cn/ChatAuth/dev/` |
| `Deploy Docs` | push to `main` | deploy formal docs to `gh-pages:/` |
| `Publish` | `v*` tag | OIDC Trusted Publishing to PyPI |

Merge is not release. Real `0.1.x+` releases require explicit user approval, a tag on the merged default-branch commit, GitHub Actions + PyPI Trusted Publisher, and PyPI JSON/simple/clean-install readback.

## Documentation standards

- Chinese is the default language; `.en.md` files are English mirrors.
- The home page is a navigation hub, not a linear development log.
- The CLI tree must come from real `chatauth --tree` output and be guarded by tests.
- Quickstart must run locally and must not depend on real CRS/OpenAI/Codex credentials.
- Public docs must not contain private paths, hostnames, Feishu/Lark IDs, token masks, or internal workspace records.

## Git and artifact standards

- Change `main` through feature branches and PRs by default.
- `dist/`, `site/`, `*.egg-info/`, `__pycache__/`, and `.pytest_cache/` must remain ignored and uncommitted.
- The default branch should use the ChatArch protection baseline: PR required, review count 0, enforce admins, force-push/delete disabled.
- After every merge/release, the local checkout should return to clean `main` synchronized with `origin/main` and tags.
