from click.testing import CliRunner

from chatauth import __version__
from chatauth.cli import cli


def test_cli_help_and_version_expose_shared_root_contract():
    runner = CliRunner()
    help_result = runner.invoke(cli, ["--help"])
    version_result = runner.invoke(cli, ["--version"])

    assert help_result.exit_code == 0, help_result.output
    assert "--tree" in help_result.output
    assert "--tree-brief" in help_result.output
    assert version_result.exit_code == 0, version_result.output
    assert f"chatauth, version {__version__}" in version_result.output


def test_cli_tree_contains_registered_chatauth_contract():
    result = CliRunner().invoke(cli, ["--tree"])

    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[0] == "chatauth"
    for expected in [
        "chatauth",
        "--version",
        "--tree",
        "--tree-brief",
        "health",
        "service",
        "init",
        "doctor",
        "admin",
        "clients",
        "subjects",
        "grants",
        "keys",
        "token",
        "import-refresh",
        "refresh",
        "--execute",
        "verify",
        "access-token",
        "without changing it",
        "exits non-zero",
        "without credentials",
        "private handoff file",
        "without private key material",
        "private token store",
        "print only valid or invalid",
    ]:
        assert expected in result.output

    assert "<NAME>" in result.output
    assert "<CLIENT-ID>" in result.output
    assert "<SUBJECT>" in result.output
    assert "[--audience AUDIENCE]" in result.output
    assert "[--token-store TOKEN-STORE]" in result.output


def test_cli_tree_brief_keeps_nodes_and_omits_signatures():
    result = CliRunner().invoke(cli, ["--tree-brief"])

    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[0] == "chatauth"
    for expected in [
        "--version",
        "--tree",
        "--tree-brief",
        "admin",
        "clients",
        "create",
        "grants",
        "issue",
        "service",
        "token",
        "refresh",
        "verify",
        "access-token",
        "private handoff file",
        "print only valid or invalid",
    ]:
        assert expected in result.output

    assert "<NAME>" not in result.output
    assert "<CLIENT-ID>" not in result.output
    assert "<SUBJECT>" not in result.output
    assert "[--audience AUDIENCE]" not in result.output
    assert "[--token-store TOKEN-STORE]" not in result.output


def test_service_run_is_reserved_and_nonzero():
    result = CliRunner().invoke(cli, ["service", "run"])
    assert result.exit_code != 0
    assert "not implemented" in result.output.lower() or "reserved" in result.output.lower()


def test_token_writes_are_dry_run_without_execute(tmp_path):
    handoff = tmp_path / "refresh.txt"
    handoff.write_text("chr_fake\n", encoding="utf-8")
    store = tmp_path / "runtime-token.json"
    result = CliRunner().invoke(
        cli,
        ["token", "import-refresh", "--state-dir", str(tmp_path / "state"), "--token-store", str(store), "--from-file", str(handoff)],
    )
    assert result.exit_code == 0, result.output
    assert "planned" in result.output
    assert not store.exists()
