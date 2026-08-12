"""ChatAuth command-line interface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import click

from . import __version__
from .operations import (
    DEFAULT_ISSUER,
    clear_token_store,
    create_client,
    create_subject,
    doctor,
    export_jwks,
    import_refresh_token,
    init_service,
    issue_refresh_grant,
    list_clients,
    list_grants,
    list_keys,
    list_subjects,
    refresh_access_token,
    token_status,
    verify_access_token,
)

TREE = """chatauth  # Self-hosted OAuth-style refresh-token auth service for ChatArch.
├── --help  # Show help.
├── --version  # Show installed version.
├── --tree  # Print the registered CLI tree.
├── health  # Check local ChatAuth state health.
├── service  # Local ChatAuth service lifecycle.
│   ├── init  # Plan/create local state DB and signing key; writes only with --execute.
│   ├── run  # Reserved ASGI service runner; currently non-zero.
│   └── doctor  # Inspect local state/config/key metadata without secrets.
├── admin  # Local admin operations.
│   ├── clients  # OAuth client registry.
│   │   ├── list  # List safe client metadata.
│   │   └── create  # Create a client; writes only with --execute.
│   ├── subjects  # Principals that can receive refresh grants.
│   │   ├── list  # List safe subject metadata.
│   │   └── create  # Create a subject; writes only with --execute.
│   ├── grants  # Refresh-token grant families.
│   │   ├── list  # List safe grant metadata.
│   │   └── issue  # Issue initial refresh token to a 0600 handoff file; writes only with --execute.
│   └── keys  # Signing keys and JWKS.
│       ├── list  # List signing-key metadata.
│       └── jwks  # Export public JWKS.
├── token  # Machine-side runtime token store operations.
│   ├── import-refresh  # Import refresh token from a handoff file; writes only with --execute.
│   ├── status  # Show token-store metadata without token values.
│   ├── refresh  # Exchange stored refresh token for access token and rotated refresh token; writes only with --execute.
│   └── clear  # Remove local runtime token store; writes only with --execute.
└── verify  # Resource-side verification helpers.
    ├── jwks  # Export public JWKS.
    └── access-token  # Verify stored access token audience/scope from local state or JWKS.
"""


def _print(data: dict[str, Any]) -> None:
    click.echo(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


def _state_option(func):
    return click.option("--state-dir", type=click.Path(path_type=Path), default=None, help="ChatAuth state directory.")(func)


def _token_store_option(func):
    return click.option("--token-store", type=click.Path(path_type=Path), required=True, help="Runtime token store JSON path.")(func)


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, invoke_without_command=True)
@click.version_option(__version__, prog_name="chatauth")
@click.option("--tree", "show_tree", is_flag=True, help="Print the registered CLI tree.")
@click.pass_context
def cli(ctx: click.Context, show_tree: bool) -> None:
    """Self-hosted OAuth-style refresh-token auth service for ChatArch."""
    if show_tree:
        click.echo(TREE)
        ctx.exit(0)


@cli.command()
@_state_option
def health(state_dir: Path | None) -> None:
    """Check local ChatAuth state health."""
    _print(doctor(state_dir=state_dir))


@cli.group()
def service() -> None:
    """Local ChatAuth service lifecycle."""


@service.command("init")
@_state_option
@click.option("--issuer", default=DEFAULT_ISSUER, show_default=True)
@click.option("--execute", is_flag=True, help="Actually create/update local state.")
def service_init(state_dir: Path | None, issuer: str, execute: bool) -> None:
    _print(init_service(state_dir=state_dir, issuer=issuer, execute=execute))


@service.command("run")
def service_run() -> None:
    raise click.ClickException("service run is reserved and not implemented in ChatAuth 0.1.x")


@service.command("doctor")
@_state_option
def service_doctor(state_dir: Path | None) -> None:
    _print(doctor(state_dir=state_dir))


@cli.group()
def admin() -> None:
    """Local admin operations."""


@admin.group()
def clients() -> None:
    """OAuth client registry."""


@clients.command("list")
@_state_option
def clients_list(state_dir: Path | None) -> None:
    _print(list_clients(state_dir=state_dir))


@clients.command("create")
@click.argument("name")
@_state_option
@click.option("--audience", required=True)
@click.option("--scope", "scopes", multiple=True)
@click.option("--execute", is_flag=True)
def clients_create(name: str, state_dir: Path | None, audience: str, scopes: tuple[str, ...], execute: bool) -> None:
    _print(create_client(state_dir=state_dir, name=name, audience=audience, scopes=scopes, execute=execute))


@admin.group()
def subjects() -> None:
    """Principals that can receive refresh grants."""


@subjects.command("list")
@_state_option
def subjects_list(state_dir: Path | None) -> None:
    _print(list_subjects(state_dir=state_dir))


@subjects.command("create")
@click.argument("subject")
@_state_option
@click.option("--display-name", default=None)
@click.option("--execute", is_flag=True)
def subjects_create(subject: str, state_dir: Path | None, display_name: str | None, execute: bool) -> None:
    _print(create_subject(state_dir=state_dir, subject=subject, display_name=display_name, execute=execute))


@admin.group()
def grants() -> None:
    """Refresh-token grant families."""


@grants.command("list")
@_state_option
def grants_list(state_dir: Path | None) -> None:
    _print(list_grants(state_dir=state_dir))


@grants.command("issue")
@click.argument("client_id")
@click.argument("subject")
@_state_option
@click.option("--audience", required=True)
@click.option("--scope", "scopes", multiple=True)
@click.option("--ttl-days", type=int, default=30, show_default=True)
@click.option("--handoff-file", type=click.Path(path_type=Path), required=True)
@click.option("--execute", is_flag=True)
def grants_issue(client_id: str, subject: str, state_dir: Path | None, audience: str, scopes: tuple[str, ...], ttl_days: int, handoff_file: Path, execute: bool) -> None:
    _print(issue_refresh_grant(state_dir=state_dir, client_id=client_id, subject=subject, audience=audience, scopes=scopes, ttl_days=ttl_days, handoff_file=handoff_file, execute=execute))


@admin.group()
def keys() -> None:
    """Signing keys and JWKS."""


@keys.command("list")
@_state_option
def keys_list(state_dir: Path | None) -> None:
    _print(list_keys(state_dir=state_dir))


@keys.command("jwks")
@_state_option
def keys_jwks(state_dir: Path | None) -> None:
    _print(export_jwks(state_dir=state_dir))


@cli.group()
def token() -> None:
    """Machine-side runtime token store operations."""


@token.command("import-refresh")
@_state_option
@_token_store_option
@click.option("--from-file", "from_file", type=click.Path(path_type=Path), required=True)
@click.option("--execute", is_flag=True)
def token_import_refresh(state_dir: Path | None, token_store: Path, from_file: Path, execute: bool) -> None:
    _print(import_refresh_token(state_dir=state_dir, token_store=token_store, from_file=from_file, execute=execute))


@token.command("status")
@_token_store_option
def token_status_cmd(token_store: Path) -> None:
    _print(token_status(token_store=token_store))


@token.command("refresh")
@_state_option
@_token_store_option
@click.option("--execute", is_flag=True)
def token_refresh(state_dir: Path | None, token_store: Path, execute: bool) -> None:
    _print(refresh_access_token(state_dir=state_dir, token_store=token_store, execute=execute))


@token.command("clear")
@_token_store_option
@click.option("--execute", is_flag=True)
def token_clear(token_store: Path, execute: bool) -> None:
    _print(clear_token_store(token_store=token_store, execute=execute))


@cli.group()
def verify() -> None:
    """Resource-side verification helpers."""


@verify.command("jwks")
@_state_option
def verify_jwks(state_dir: Path | None) -> None:
    _print(export_jwks(state_dir=state_dir))


@verify.command("access-token")
@_state_option
@_token_store_option
@click.option("--audience", required=True)
@click.option("--scope", "scopes", multiple=True)
@click.option("--jwks-file", type=click.Path(path_type=Path), default=None, help="Public JWKS JSON file for resource-side verification without issuer private key access.")
@click.option("--issuer", default=None, help="Expected issuer when verifying with --jwks-file.")
def verify_access_token_cmd(state_dir: Path | None, token_store: Path, audience: str, scopes: tuple[str, ...], jwks_file: Path | None, issuer: str | None) -> None:
    jwks = None
    if jwks_file is not None:
        jwks = json.loads(jwks_file.read_text(encoding="utf-8"))
    result = verify_access_token(state_dir=state_dir, token_store=token_store, audience=audience, scopes=scopes, jwks=jwks, issuer=issuer)
    click.echo("valid" if result["valid"] else "invalid")
    if not result["valid"]:
        raise click.exceptions.Exit(1)


if __name__ == "__main__":  # pragma: no cover
    cli()
