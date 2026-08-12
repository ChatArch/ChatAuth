import json
import os
import stat

import pytest
from click.testing import CliRunner

import chatauth.operations as ops
from chatauth.cli import cli
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


def _bootstrap_grant(tmp_path, *, audience="chatarch.internal", scopes=("agent:run",)):
    state_dir = tmp_path / "state"
    handoff = tmp_path / "handoff.txt"
    token_store = tmp_path / "token-store.json"
    init_service(state_dir=state_dir, issuer="https://auth.example.test", execute=True)
    client = create_client(
        state_dir=state_dir,
        name="demo",
        audience="chatarch.internal",
        scopes=["agent:run", "agent:read"],
        execute=True,
    )
    create_subject(state_dir=state_dir, subject="machine:demo", execute=True)
    issue_refresh_grant(
        state_dir=state_dir,
        client_id=client["client_id"],
        subject="machine:demo",
        audience=audience,
        scopes=scopes,
        handoff_file=handoff,
        execute=True,
    )
    import_refresh_token(state_dir=state_dir, token_store=token_store, from_file=handoff, execute=True)
    refresh_access_token(state_dir=state_dir, token_store=token_store, execute=True)
    return state_dir, handoff, token_store, client


def test_access_token_verification_uses_public_jwks_without_private_key(tmp_path):
    state_dir, _handoff, token_store, _client = _bootstrap_grant(tmp_path)
    jwks = export_jwks(state_dir=state_dir)
    jwks_file = tmp_path / "jwks.json"
    jwks_file.write_text(json.dumps(jwks), encoding="utf-8")
    (state_dir / "signing-key.pem").rename(state_dir / "issuer-private-key.removed")

    verified = verify_access_token(
        state_dir=None,
        token_store=token_store,
        audience="chatarch.internal",
        scopes=["agent:run"],
        jwks=jwks,
        issuer="https://auth.example.test",
    )
    assert verified["valid"] is True

    cli_result = CliRunner().invoke(
        cli,
        [
            "verify",
            "access-token",
            "--token-store",
            str(token_store),
            "--jwks-file",
            str(jwks_file),
            "--issuer",
            "https://auth.example.test",
            "--audience",
            "chatarch.internal",
            "--scope",
            "agent:run",
        ],
    )
    assert cli_result.exit_code == 0, cli_result.output
    assert cli_result.output.strip() == "valid"


def test_issue_refresh_grant_rejects_audience_and_scopes_outside_client_contract(tmp_path):
    state_dir = tmp_path / "state"
    init_service(state_dir=state_dir, execute=True)
    client = create_client(
        state_dir=state_dir,
        name="demo",
        audience="chatarch.internal",
        scopes=["agent:run"],
        execute=True,
    )
    create_subject(state_dir=state_dir, subject="machine:demo", execute=True)

    with pytest.raises(RuntimeError, match="audience"):
        issue_refresh_grant(
            state_dir=state_dir,
            client_id=client["client_id"],
            subject="machine:demo",
            audience="other.internal",
            scopes=["agent:run"],
            execute=True,
        )

    with pytest.raises(RuntimeError, match="scope"):
        issue_refresh_grant(
            state_dir=state_dir,
            client_id=client["client_id"],
            subject="machine:demo",
            audience="chatarch.internal",
            scopes=["admin:all"],
            execute=True,
        )


def test_sensitive_state_handoff_and_token_files_are_created_or_replaced_private(tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    key_file = state_dir / "signing-key.pem"
    key_file.write_text("existing-key-placeholder", encoding="utf-8")
    key_file.chmod(0o644)
    init_service(state_dir=state_dir, execute=True)
    assert stat.S_IMODE(key_file.stat().st_mode) == 0o600
    assert stat.S_IMODE((state_dir / "chatauth.sqlite3").stat().st_mode) == 0o600

    symlink_state = tmp_path / "symlink-state"
    symlink_state.mkdir()
    symlink_target = tmp_path / "leaked-key-target.pem"
    symlink_target.write_text("target", encoding="utf-8")
    (symlink_state / "signing-key.pem").symlink_to(symlink_target)
    with pytest.raises(RuntimeError, match="symlink"):
        init_service(state_dir=symlink_state, execute=True)

    client = create_client(state_dir=state_dir, name="demo", audience="chatarch.internal", scopes=["agent:run"], execute=True)
    create_subject(state_dir=state_dir, subject="machine:demo", execute=True)
    handoff = tmp_path / "handoff.txt"
    handoff.write_text("old\n", encoding="utf-8")
    handoff.chmod(0o644)
    issue_refresh_grant(
        state_dir=state_dir,
        client_id=client["client_id"],
        subject="machine:demo",
        audience="chatarch.internal",
        scopes=["agent:run"],
        handoff_file=handoff,
        execute=True,
    )
    assert stat.S_IMODE(handoff.stat().st_mode) == 0o600

    leak = tmp_path / "leak.txt"
    leak.write_text("do-not-touch", encoding="utf-8")
    token_store = tmp_path / "token-store.json"
    (tmp_path / "token-store.json.tmp").symlink_to(leak)
    import_refresh_token(state_dir=state_dir, token_store=token_store, from_file=handoff, execute=True)
    assert leak.read_text(encoding="utf-8") == "do-not-touch"
    assert not token_store.is_symlink()
    assert stat.S_IMODE(token_store.stat().st_mode) == 0o600


def test_refresh_rotation_rolls_back_database_if_token_store_write_fails(tmp_path, monkeypatch):
    state_dir, _handoff, token_store, _client = _bootstrap_grant(tmp_path)
    old_store = json.loads(token_store.read_text(encoding="utf-8"))
    old_refresh = old_store["refresh_token"]

    def fail_write(path, payload):
        raise OSError("simulated token-store write failure")

    original_write_private_json = ops._write_private_json
    monkeypatch.setattr(ops, "_write_private_json", fail_write)
    with pytest.raises(OSError, match="simulated"):
        refresh_access_token(state_dir=state_dir, token_store=token_store, execute=True)

    monkeypatch.setattr(ops, "_write_private_json", original_write_private_json)
    store_after_failure = json.loads(token_store.read_text(encoding="utf-8"))
    assert store_after_failure["refresh_token"] == old_refresh

    refreshed = refresh_access_token(state_dir=state_dir, token_store=token_store, execute=True)
    assert refreshed["refresh_token_rotated"] is True
    assert json.loads(token_store.read_text(encoding="utf-8"))["refresh_token"] != old_refresh
