"""Core ChatAuth operations.

The CLI is intentionally a thin adapter over these importable functions.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import stat
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

DEFAULT_ISSUER = "https://auth.local.chatarch.test"
DB_NAME = "chatauth.sqlite3"
PRIVATE_KEY_NAME = "signing-key.pem"
TOKEN_STORE_SCHEMA = 1


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _from_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding_len = (-len(value)) % 4
    return base64.urlsafe_b64decode((value + "=" * padding_len).encode("ascii"))


def _json_b64(payload: dict[str, Any]) -> str:
    return _b64url(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def _token(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(32)}"


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _scopes(scopes: Iterable[str] | None) -> list[str]:
    return sorted({scope for scope in (scopes or []) if scope})


def _state_dir(path: str | os.PathLike[str] | Path | None) -> Path:
    if path is None:
        return Path.home() / ".chatarch" / "chatauth"
    return Path(path).expanduser()


def _db_path(state_dir: str | os.PathLike[str] | Path | None) -> Path:
    return _state_dir(state_dir) / DB_NAME


def _key_path(state_dir: str | os.PathLike[str] | Path | None) -> Path:
    return _state_dir(state_dir) / PRIVATE_KEY_NAME


def _connect(state_dir: str | os.PathLike[str] | Path | None) -> sqlite3.Connection:
    path = _db_path(state_dir)
    if path.is_symlink():
        raise RuntimeError("ChatAuth database path must not be a symlink")
    conn = sqlite3.connect(path)
    try:
        path.chmod(0o600)
    except PermissionError:
        pass
    conn.row_factory = sqlite3.Row
    return conn


def _secure_open_private(path: Path) -> int:
    if path.is_symlink():
        raise RuntimeError(f"sensitive file path must not be a symlink: {path}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    os.fchmod(fd, 0o600)
    return fd


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS clients (
          client_id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          audience TEXT NOT NULL,
          scopes_json TEXT NOT NULL,
          enabled INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS subjects (
          subject TEXT PRIMARY KEY,
          display_name TEXT NOT NULL,
          enabled INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS grants (
          grant_id TEXT PRIMARY KEY,
          client_id TEXT NOT NULL,
          subject TEXT NOT NULL,
          audience TEXT NOT NULL,
          scopes_json TEXT NOT NULL,
          refresh_hash TEXT NOT NULL,
          expires_at TEXT NOT NULL,
          revoked_at TEXT,
          created_at TEXT NOT NULL,
          rotated_at TEXT,
          FOREIGN KEY(client_id) REFERENCES clients(client_id),
          FOREIGN KEY(subject) REFERENCES subjects(subject)
        );
        CREATE INDEX IF NOT EXISTS idx_grants_refresh_hash ON grants(refresh_hash);
        CREATE TABLE IF NOT EXISTS signing_keys (
          kid TEXT PRIMARY KEY,
          alg TEXT NOT NULL,
          active INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL
        );
        """
    )
    conn.commit()


def _ensure_service(state_dir: str | os.PathLike[str] | Path | None) -> None:
    if not _db_path(state_dir).exists():
        raise RuntimeError("ChatAuth state is not initialized; run `chatauth service init --execute` first")


def _set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute("INSERT OR REPLACE INTO meta(key, value) VALUES(?, ?)", (key, value))


def _get_meta(conn: sqlite3.Connection, key: str, default: str | None = None) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    if row is None:
        return default
    return str(row["value"])


def _load_private_key(state_dir: str | os.PathLike[str] | Path | None) -> rsa.RSAPrivateKey:
    path = _key_path(state_dir)
    return serialization.load_pem_private_key(path.read_bytes(), password=None)  # type: ignore[return-value]


def _public_jwk(private_key: rsa.RSAPrivateKey, kid: str) -> dict[str, str]:
    return _public_key_jwk(private_key.public_key(), kid)


def _public_key_jwk(public_key: rsa.RSAPublicKey, kid: str) -> dict[str, str]:
    numbers = public_key.public_numbers()
    return {
        "kty": "RSA",
        "use": "sig",
        "kid": kid,
        "alg": "RS256",
        "n": _b64url(numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, "big")),
        "e": _b64url(numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, "big")),
    }


def _public_key_from_jwk(jwk: dict[str, Any]) -> rsa.RSAPublicKey:
    if jwk.get("kty") != "RSA" or jwk.get("alg") != "RS256":
        raise RuntimeError("JWKS key must be RSA RS256")
    n = int.from_bytes(_b64url_decode(str(jwk["n"])), "big")
    e = int.from_bytes(_b64url_decode(str(jwk["e"])), "big")
    return rsa.RSAPublicNumbers(e=e, n=n).public_key()


def init_service(*, state_dir: str | os.PathLike[str] | Path | None = None, issuer: str = DEFAULT_ISSUER, execute: bool = False) -> dict[str, Any]:
    root = _state_dir(state_dir)
    if not execute:
        return {"changed": False, "planned": True, "state_dir": str(root), "issuer": issuer}

    root.mkdir(parents=True, exist_ok=True)
    try:
        root.chmod(0o700)
    except PermissionError:
        pass
    conn = _connect(root)
    _init_schema(conn)
    created_key = False
    kid = "main"
    key_file = _key_path(root)
    if key_file.is_symlink():
        raise RuntimeError("ChatAuth signing key path must not be a symlink")
    if not key_file.exists():
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        key_bytes = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        fd = _secure_open_private(key_file)
        with os.fdopen(fd, "wb") as fh:
            fh.write(key_bytes)
        created_key = True
    else:
        try:
            key_file.chmod(0o600)
        except PermissionError:
            pass
    _set_meta(conn, "issuer", issuer)
    _set_meta(conn, "created_at", _get_meta(conn, "created_at") or _iso(_now()))
    conn.execute(
        "INSERT OR REPLACE INTO signing_keys(kid, alg, active, created_at) VALUES(?, ?, 1, COALESCE((SELECT created_at FROM signing_keys WHERE kid = ?), ?))",
        (kid, "RS256", kid, _iso(_now())),
    )
    conn.commit()
    return {"changed": True, "state_dir": str(root), "issuer": issuer, "db_path": str(_db_path(root)), "created_key": created_key, "kid": kid}


def doctor(*, state_dir: str | os.PathLike[str] | Path | None = None) -> dict[str, Any]:
    db = _db_path(state_dir)
    key = _key_path(state_dir)
    ok = db.exists() and key.exists()
    result: dict[str, Any] = {"ok": ok, "state_dir": str(_state_dir(state_dir)), "db_exists": db.exists(), "key_exists": key.exists()}
    if ok:
        with _connect(state_dir) as conn:
            result["issuer"] = _get_meta(conn, "issuer", DEFAULT_ISSUER)
            result["clients"] = conn.execute("SELECT COUNT(*) AS n FROM clients").fetchone()["n"]
            result["subjects"] = conn.execute("SELECT COUNT(*) AS n FROM subjects").fetchone()["n"]
            result["grants"] = conn.execute("SELECT COUNT(*) AS n FROM grants").fetchone()["n"]
    return result


def create_client(*, state_dir: str | os.PathLike[str] | Path | None, name: str, audience: str, scopes: Iterable[str] | None = None, execute: bool = False) -> dict[str, Any]:
    if not execute:
        return {"planned": True, "changed": False, "name": name, "audience": audience, "scopes": _scopes(scopes)}
    _ensure_service(state_dir)
    client_id = "client_" + secrets.token_urlsafe(12)
    with _connect(state_dir) as conn:
        conn.execute(
            "INSERT INTO clients(client_id, name, audience, scopes_json, enabled, created_at) VALUES(?, ?, ?, ?, 1, ?)",
            (client_id, name, audience, json.dumps(_scopes(scopes)), _iso(_now())),
        )
        conn.commit()
    return {"changed": True, "client_id": client_id, "name": name, "audience": audience, "scopes": _scopes(scopes), "enabled": True}


def create_subject(*, state_dir: str | os.PathLike[str] | Path | None, subject: str, display_name: str | None = None, execute: bool = False) -> dict[str, Any]:
    if not execute:
        return {"planned": True, "changed": False, "subject": subject, "display_name": display_name or subject}
    _ensure_service(state_dir)
    with _connect(state_dir) as conn:
        conn.execute(
            "INSERT INTO subjects(subject, display_name, enabled, created_at) VALUES(?, ?, 1, ?)",
            (subject, display_name or subject, _iso(_now())),
        )
        conn.commit()
    return {"changed": True, "subject": subject, "display_name": display_name or subject, "enabled": True}


def issue_refresh_grant(
    *,
    state_dir: str | os.PathLike[str] | Path | None,
    client_id: str,
    subject: str,
    audience: str,
    scopes: Iterable[str] | None = None,
    ttl_days: int = 30,
    handoff_file: str | os.PathLike[str] | Path | None = None,
    execute: bool = False,
) -> dict[str, Any]:
    if not execute:
        return {"planned": True, "changed": False, "client_id": client_id, "subject": subject, "audience": audience, "scopes": _scopes(scopes), "ttl_days": ttl_days}
    _ensure_service(state_dir)
    grant_id = "grant_" + secrets.token_urlsafe(12)
    refresh = _token("chr")
    expires_at = _now() + timedelta(days=ttl_days)
    with _connect(state_dir) as conn:
        client = conn.execute("SELECT * FROM clients WHERE client_id = ? AND enabled = 1", (client_id,)).fetchone()
        if client is None:
            raise RuntimeError(f"unknown or disabled client: {client_id}")
        if audience != client["audience"]:
            raise RuntimeError("grant audience must match the client audience")
        requested_scopes = _scopes(scopes)
        allowed_scopes = set(json.loads(client["scopes_json"]))
        if not set(requested_scopes).issubset(allowed_scopes):
            raise RuntimeError("grant scope must be allowed by the client")
        subj = conn.execute("SELECT * FROM subjects WHERE subject = ? AND enabled = 1", (subject,)).fetchone()
        if subj is None:
            raise RuntimeError(f"unknown or disabled subject: {subject}")
        conn.execute(
            "INSERT INTO grants(grant_id, client_id, subject, audience, scopes_json, refresh_hash, expires_at, created_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
            (grant_id, client_id, subject, audience, json.dumps(requested_scopes), _hash_token(refresh), _iso(expires_at), _iso(_now())),
        )
        conn.commit()
    written = False
    if handoff_file is not None:
        path = Path(handoff_file).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = _secure_open_private(path)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(refresh + "\n")
        written = True
    return {"changed": True, "grant_id": grant_id, "client_id": client_id, "subject": subject, "audience": audience, "scopes": _scopes(scopes), "expires_at": _iso(expires_at), "refresh_token_written": written}


def import_refresh_token(*, state_dir: str | os.PathLike[str] | Path | None, token_store: str | os.PathLike[str] | Path, from_file: str | os.PathLike[str] | Path, execute: bool = False) -> dict[str, Any]:
    if not execute:
        return {"planned": True, "changed": False, "token_store": str(Path(token_store).expanduser()), "refresh_token_set": False, "access_token_set": False}
    _ensure_service(state_dir)
    refresh = Path(from_file).expanduser().read_text(encoding="utf-8").strip()
    if not refresh.startswith("chr_"):
        raise RuntimeError("refresh token handoff has invalid prefix")
    path = Path(token_store).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": TOKEN_STORE_SCHEMA, "refresh_token": refresh, "access_token": None, "access_token_expires_at": None, "updated_at": _iso(_now())}
    _write_private_json(path, payload)
    return {"changed": True, "token_store": str(path), "refresh_token_set": True, "access_token_set": False}


def _write_private_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.parent / f".{path.name}.{secrets.token_urlsafe(8)}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(tmp, flags, 0o600)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, path)
        try:
            path.chmod(0o600)
        except PermissionError:
            pass
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        raise


def _load_store(token_store: str | os.PathLike[str] | Path) -> dict[str, Any]:
    path = Path(token_store).expanduser()
    if not path.exists():
        raise RuntimeError("token store does not exist; import a refresh token first")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("token store must be a JSON object")
    return data


def _sign_access_token(*, state_dir: str | os.PathLike[str] | Path | None, client_id: str, subject: str, audience: str, scopes: list[str], ttl_seconds: int = 3600) -> tuple[str, str]:
    with _connect(state_dir) as conn:
        issuer = _get_meta(conn, "issuer", DEFAULT_ISSUER) or DEFAULT_ISSUER
        key_row = conn.execute("SELECT kid FROM signing_keys WHERE active = 1 ORDER BY created_at DESC LIMIT 1").fetchone()
        kid = key_row["kid"] if key_row else "main"
    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT", "kid": kid}
    payload = {
        "iss": issuer,
        "sub": subject,
        "aud": audience,
        "scope": " ".join(scopes),
        "client_id": client_id,
        "jti": _token("jti"),
        "iat": now,
        "exp": now + ttl_seconds,
    }
    signing_input = f"{_json_b64(header)}.{_json_b64(payload)}".encode("ascii")
    key = _load_private_key(state_dir)
    signature = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    return signing_input.decode("ascii") + "." + _b64url(signature), _iso(datetime.fromtimestamp(now + ttl_seconds, tz=timezone.utc))


def refresh_access_token(*, state_dir: str | os.PathLike[str] | Path | None, token_store: str | os.PathLike[str] | Path, execute: bool = False) -> dict[str, Any]:
    if not execute:
        return {"planned": True, "changed": False, "token_store": str(Path(token_store).expanduser()), "refresh_token_rotated": False, "access_token_set": False}
    _ensure_service(state_dir)
    path = Path(token_store).expanduser()
    data = _load_store(path)
    refresh = data.get("refresh_token")
    if not isinstance(refresh, str) or not refresh.startswith("chr_"):
        raise RuntimeError("token store has no valid refresh token")
    now_iso = _iso(_now())
    with _connect(state_dir) as conn:
        conn.execute("BEGIN IMMEDIATE")
        grant = conn.execute("SELECT * FROM grants WHERE refresh_hash = ? AND revoked_at IS NULL", (_hash_token(refresh),)).fetchone()
        if grant is None:
            conn.rollback()
            raise RuntimeError("refresh token is unknown, revoked, or already rotated")
        if _from_iso(grant["expires_at"]) <= _now():
            conn.rollback()
            raise RuntimeError("refresh token is expired")
        scopes = json.loads(grant["scopes_json"])
        access_token, access_expires = _sign_access_token(state_dir=state_dir, client_id=grant["client_id"], subject=grant["subject"], audience=grant["audience"], scopes=scopes)
        new_refresh = _token("chr")
        cur = conn.execute(
            "UPDATE grants SET refresh_hash = ?, rotated_at = ? WHERE grant_id = ? AND refresh_hash = ? AND revoked_at IS NULL",
            (_hash_token(new_refresh), now_iso, grant["grant_id"], _hash_token(refresh)),
        )
        if cur.rowcount != 1:
            conn.rollback()
            raise RuntimeError("refresh token rotation conflict")
        data.update({"refresh_token": new_refresh, "access_token": access_token, "access_token_expires_at": access_expires, "updated_at": now_iso})
        _write_private_json(path, data)
        conn.commit()
    return {"changed": True, "token_store": str(path), "refresh_token_rotated": True, "access_token_set": True, "access_token_expires_at": access_expires}


def token_status(*, token_store: str | os.PathLike[str] | Path) -> dict[str, Any]:
    path = Path(token_store).expanduser()
    if not path.exists():
        return {"exists": False, "refresh_token_set": False, "access_token_set": False}
    data = _load_store(path)
    return {"exists": True, "token_store": str(path), "refresh_token_set": bool(data.get("refresh_token")), "access_token_set": bool(data.get("access_token")), "access_token_expires_at": data.get("access_token_expires_at")}


def clear_token_store(*, token_store: str | os.PathLike[str] | Path, execute: bool = False) -> dict[str, Any]:
    path = Path(token_store).expanduser()
    if not execute:
        return {"planned": True, "changed": False, "token_store": str(path), "exists": path.exists()}
    existed = path.exists()
    if existed:
        path.unlink()
    return {"changed": existed, "token_store": str(path), "exists": False}


def export_jwks(*, state_dir: str | os.PathLike[str] | Path | None) -> dict[str, Any]:
    _ensure_service(state_dir)
    with _connect(state_dir) as conn:
        row = conn.execute("SELECT kid FROM signing_keys WHERE active = 1 ORDER BY created_at DESC LIMIT 1").fetchone()
        kid = row["kid"] if row else "main"
    key = _load_private_key(state_dir)
    return {"keys": [_public_jwk(key, kid)]}


def verify_access_token(
    *,
    state_dir: str | os.PathLike[str] | Path | None,
    token_store: str | os.PathLike[str] | Path,
    audience: str,
    scopes: Iterable[str] | None = None,
    jwks: dict[str, Any] | None = None,
    issuer: str | None = None,
) -> dict[str, Any]:
    if jwks is None:
        _ensure_service(state_dir)
    token = _load_store(token_store).get("access_token")
    if not isinstance(token, str):
        raise RuntimeError("token store has no access token")
    parts = token.split(".")
    if len(parts) != 3:
        raise RuntimeError("access token must be a JWT")
    signing_input = f"{parts[0]}.{parts[1]}".encode("ascii")
    signature = _b64url_decode(parts[2])
    header = json.loads(_b64url_decode(parts[0]))
    payload = json.loads(_b64url_decode(parts[1]))
    kid = header.get("kid")
    if jwks is None:
        key = _load_private_key(state_dir).public_key()
    else:
        keys = [key for key in jwks.get("keys", []) if isinstance(key, dict) and key.get("kid") == kid]
        if not keys:
            raise RuntimeError("JWKS has no matching key for access token kid")
        key = _public_key_from_jwk(keys[0])
    try:
        key.verify(signature, signing_input, padding.PKCS1v15(), hashes.SHA256())
    except Exception as exc:  # pragma: no cover - backend exception types vary
        raise RuntimeError("access token signature verification failed") from exc
    if issuer is None:
        if state_dir is None:
            raise RuntimeError("issuer is required when verifying with JWKS without local state")
        with _connect(state_dir) as conn:
            issuer = _get_meta(conn, "issuer", DEFAULT_ISSUER)
    required_scopes = set(_scopes(scopes))
    token_scopes = set(str(payload.get("scope", "")).split())
    valid = (
        header.get("alg") == "RS256"
        and payload.get("iss") == issuer
        and payload.get("aud") == audience
        and int(payload.get("exp", 0)) > int(time.time())
        and required_scopes.issubset(token_scopes)
    )
    return {"valid": valid, "subject": payload.get("sub"), "client_id": payload.get("client_id"), "audience": payload.get("aud"), "scopes": sorted(token_scopes), "kid": kid}


def list_clients(*, state_dir: str | os.PathLike[str] | Path | None) -> dict[str, Any]:
    _ensure_service(state_dir)
    with _connect(state_dir) as conn:
        rows = conn.execute("SELECT client_id, name, audience, scopes_json, enabled, created_at FROM clients ORDER BY created_at").fetchall()
    return {"clients": [{**dict(row), "scopes": json.loads(row["scopes_json"])} for row in rows]}


def list_subjects(*, state_dir: str | os.PathLike[str] | Path | None) -> dict[str, Any]:
    _ensure_service(state_dir)
    with _connect(state_dir) as conn:
        rows = conn.execute("SELECT subject, display_name, enabled, created_at FROM subjects ORDER BY created_at").fetchall()
    return {"subjects": [dict(row) for row in rows]}


def list_grants(*, state_dir: str | os.PathLike[str] | Path | None) -> dict[str, Any]:
    _ensure_service(state_dir)
    with _connect(state_dir) as conn:
        rows = conn.execute("SELECT grant_id, client_id, subject, audience, scopes_json, expires_at, revoked_at, created_at, rotated_at FROM grants ORDER BY created_at").fetchall()
    return {"grants": [{**dict(row), "scopes": json.loads(row["scopes_json"])} for row in rows]}


def list_keys(*, state_dir: str | os.PathLike[str] | Path | None) -> dict[str, Any]:
    _ensure_service(state_dir)
    with _connect(state_dir) as conn:
        rows = conn.execute("SELECT kid, alg, active, created_at FROM signing_keys ORDER BY created_at").fetchall()
    return {"keys": [dict(row) for row in rows]}
