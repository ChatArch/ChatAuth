from pathlib import Path
import re

from click.testing import CliRunner

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

from chatauth.cli import cli

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _text_fences(markdown: str) -> list[str]:
    return [match.strip() for match in re.findall(r"```text\n(.*?)\n```", markdown, flags=re.DOTALL)]


def _runtime_tree(option: str) -> str:
    result = CliRunner().invoke(cli, [option])
    assert result.exit_code == 0, result.output
    return result.output.strip()


def test_documented_cli_trees_match_registered_runtime_trees():
    expected = [_runtime_tree("--tree"), _runtime_tree("--tree-brief")]
    assert _text_fences(_read("docs/cli-tree.md"))[:2] == expected
    assert _text_fences(_read("docs/cli-tree.en.md"))[:2] == expected


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
    assert "chatstyle>=0.2.0,<0.3.0" in data["project"]["dependencies"]
    docs = data["project"]["optional-dependencies"]["docs"]
    for requirement in docs:
        assert ">=" in requirement and "<" in requirement, requirement
    assert any(requirement.startswith("mkdocs>=") for requirement in docs)
    assert "mkdocs-material>=9.5,<9.7" in docs
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
    assert "chatauth --version" in ci
    assert "chatauth --tree" in ci
    assert "chatauth --tree-brief" in ci
    assert _read(".github/workflows/preview-docs.yml")
    assert _read(".github/workflows/deploy-docs.yml")


def test_development_guide_records_shared_cli_and_release_gates():
    develop = _read("DEVELOP.md")
    assert "chatstyle>=0.2.0,<0.3.0" in develop
    assert "add_tree_option()" in develop
    assert "chatauth --version" in develop
    assert "chatauth --tree" in develop
    assert "chatauth --tree-brief" in develop
    assert "python -m build" in develop
    assert "python -m twine check dist/*" in develop
