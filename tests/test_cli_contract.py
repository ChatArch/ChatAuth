from click.testing import CliRunner

from chatauth.cli import cli


def test_cli_tree_contains_chatauth_contract():
    result = CliRunner().invoke(cli, ["--tree"])
    assert result.exit_code == 0, result.output
    output = result.output
    for expected in [
        "chatauth",
        "--version",
        "--tree",
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
    ]:
        assert expected in output


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
