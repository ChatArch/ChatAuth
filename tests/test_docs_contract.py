from pathlib import Path
import re

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

from chatauth.cli import TREE

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _first_text_fence(markdown: str) -> str:
    match = re.search(r"```text\n(?P<body>.*?)\n```", markdown, flags=re.DOTALL)
    assert match, "missing text fenced block"
    return match.group("body").strip()


def test_documented_cli_tree_matches_runtime_tree():
    assert _first_text_fence(_read("docs/cli-tree.md")) == TREE.strip()
    assert _first_text_fence(_read("docs/cli-tree.en.md")) == TREE.strip()


def test_quickstart_documents_jwks_verify_and_execute_boundary():
    for path in ["README.md", "README.en.md", "docs/quickstart.md", "docs/quickstart.en.md"]:
        content = _read(path)
        assert "--execute" in content
        assert "--jwks-file" in content
        assert "https://auth.example.test" in content
        assert "chatauth verify access-token" in content


def test_pyproject_docs_metadata_and_bounded_docs_extra():
    data = tomllib.loads(_read("pyproject.toml"))
    urls = data["project"]["urls"]
    assert urls["Documentation"] == "https://arch.gh.wzhecnu.cn/ChatAuth/"
    docs = data["project"]["optional-dependencies"]["docs"]
    for requirement in docs:
        assert ">=" in requirement and "<" in requirement, requirement
    assert any(requirement.startswith("mkdocs>=") for requirement in docs)
    assert any(requirement.startswith("mkdocs-material>=") for requirement in docs)
    assert any(requirement.startswith("mkdocs-static-i18n>=") for requirement in docs)
    assert any(requirement.startswith("mike>=") for requirement in docs)
    dev = data["project"]["optional-dependencies"]["dev"]
    assert 'tomli>=2.0,<3.0; python_version < "3.11"' in dev


def test_mkdocs_and_ci_include_docs_gate():
    mkdocs = _read("mkdocs.yml")
    assert "site_url: https://arch.gh.wzhecnu.cn/ChatAuth/" in mkdocs
    assert "- i18n:" in mkdocs
    assert "docs_structure: suffix" in mkdocs
    assert "docs/cli-tree.md" not in mkdocs
    ci = _read(".github/workflows/ci.yml")
    assert ".[dev,docs]" in ci
    assert "mkdocs build --strict" in ci
    assert _read(".github/workflows/preview-docs.yml")
    assert _read(".github/workflows/deploy-docs.yml")
