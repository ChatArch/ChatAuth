# Development Guide

## CLI contract

- Keep the public Click root explicitly named `chatauth`.
- Use `chatstyle>=0.2.0,<0.3.0` and ChatStyle's `add_tree_option()` for the registered command tree.
- Preserve top-level `--version`, `--tree`, and `--tree-brief`; the full tree includes signatures and the brief tree omits them while retaining the same nodes and descriptions.
- Give every visible group and leaf a one-line description that states its output or mutation boundary.
- Keep command bodies as thin adapters over reusable functions in `chatauth.operations`.

## Safety contract

- Mutating commands remain dry-run unless the caller explicitly supplies `--execute`.
- Never print refresh tokens, access tokens, private signing keys, or credential values.
- Preserve private file modes, symlink rejection, refresh-token rotation, and database/token-store rollback guarantees.
- `service run` must continue to exit non-zero until a real service implementation and tests are added.

## Local gates

```bash
python -m pip install -e '.[dev,docs]'
python -m pytest -q
mkdocs build --strict
python -m build
python -m twine check dist/*
chatauth --version
chatauth --tree
chatauth --tree-brief
git diff --check
```

Keep `README.md`, `README.en.md`, `docs/`, tests, workflows, and `CHANGELOG.md` synchronized with user-visible CLI changes. Releases follow PR, green checks, squash merge, a tag on the merged default-branch commit, trusted publishing, and clean PyPI install readback.
