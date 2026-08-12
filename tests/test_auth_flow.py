import base64
import json
import stat

from chatauth.operations import (
    create_client,
    create_subject,
    doctor,
    export_jwks,
    import_refresh_token,
    init_service,
    issue_refresh_grant,
    refresh_access_token,
    verify_access_token,
)


def _decode_jwt_part(value: str) -> bytes:
    value += "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode(value.encode("ascii"))


def test_local_refresh_token_flow_rotates_and_verifies_access_token(tmp_path):
    state_dir = tmp_path / "state"
    token_store = tmp_path / "runtime-token.json"
    handoff = tmp_path / "refresh-token.txt"

    init_result = init_service(state_dir=state_dir, issuer="https://auth.example.test", execute=True)
    assert init_result["changed"] is True
    assert (state_dir / "chatauth.sqlite3").exists()
    assert doctor(state_dir=state_dir)["ok"] is True

    client = create_client(
        state_dir=state_dir,
        name="demo",
        audience="chatarch.internal",
        scopes=["agent:run"],
        execute=True,
    )
    assert client["client_id"].startswith("client_")
    assert "client_secret" not in client

    subject = create_subject(state_dir=state_dir, subject="machine:demo", execute=True)
    assert subject["subject"] == "machine:demo"

    grant = issue_refresh_grant(
        state_dir=state_dir,
        client_id=client["client_id"],
        subject="machine:demo",
        audience="chatarch.internal",
        scopes=["agent:run"],
        ttl_days=30,
        handoff_file=handoff,
        execute=True,
    )
    assert grant["refresh_token_written"] is True
    assert "refresh_token" not in grant
    assert stat.S_IMODE(handoff.stat().st_mode) == 0o600
    raw_refresh = handoff.read_text(encoding="utf-8").strip()
    assert raw_refresh.startswith("chr_")

    imported = import_refresh_token(state_dir=state_dir, token_store=token_store, from_file=handoff, execute=True)
    assert imported["refresh_token_set"] is True
    assert "refresh_token" not in imported

    refreshed = refresh_access_token(state_dir=state_dir, token_store=token_store, execute=True)
    assert refreshed["access_token_set"] is True
    assert refreshed["refresh_token_rotated"] is True
    assert "access_token" not in refreshed
    assert "refresh_token" not in refreshed

    stored = json.loads(token_store.read_text(encoding="utf-8"))
    assert stored["refresh_token"].startswith("chr_")
    assert stored["refresh_token"] != raw_refresh
    assert stored["access_token"].count(".") == 2
    payload = json.loads(_decode_jwt_part(stored["access_token"].split(".")[1]))
    assert {"iss", "aud", "sub", "client_id", "scope", "jti", "iat", "exp"}.issubset(payload)

    stale_store = tmp_path / "stale-token.json"
    stale_store.write_text(json.dumps({"schema_version": 1, "refresh_token": raw_refresh}), encoding="utf-8")
    try:
        refresh_access_token(state_dir=state_dir, token_store=stale_store, execute=True)
    except RuntimeError as exc:
        assert "already rotated" in str(exc) or "unknown" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("stale refresh token should not replay")

    jwks = export_jwks(state_dir=state_dir)
    assert jwks["keys"][0]["kty"] == "RSA"
    assert "d" not in jwks["keys"][0]

    verified = verify_access_token(
        state_dir=state_dir,
        token_store=token_store,
        audience="chatarch.internal",
        scopes=["agent:run"],
    )
    assert verified["valid"] is True
    assert verified["subject"] == "machine:demo"
    assert verified["client_id"] == client["client_id"]
