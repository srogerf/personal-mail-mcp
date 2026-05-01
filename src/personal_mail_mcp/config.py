from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "accounts.toml"
DEFAULT_AUTH_CONFIG_PATH = PROJECT_ROOT / "config" / "auth.toml"
DEFAULT_MAIL_RULES_PATH = PROJECT_ROOT / "config" / "mail_rules.default.toml"
LOCAL_MAIL_RULES_PATH = PROJECT_ROOT / "config" / "mail_rules.local.toml"
TOKEN_DIR = PROJECT_ROOT / ".tokens"


@dataclass(frozen=True)
class Account:
    id: str
    provider: str
    email: str
    calendar: bool = False


@dataclass(frozen=True)
class MicrosoftAuthConfig:
    client_id: str
    tenant: str = "common"


@dataclass(frozen=True)
class GoogleAuthConfig:
    client_secrets_file: Path


def load_accounts(path: Path = DEFAULT_CONFIG_PATH) -> list[Account]:
    if not path.exists():
        return []

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    accounts = []
    for item in data.get("accounts", []):
        accounts.append(
            Account(
                id=str(item["id"]),
                provider=str(item["provider"]),
                email=str(item["email"]),
                calendar=bool(item.get("calendar", False)),
            )
        )
    return accounts


def get_account(account_id: str) -> Account:
    for account in load_accounts():
        if account.id == account_id:
            return account
    raise ValueError(f"Unknown account id: {account_id}")


def _load_auth_data(path: Path = DEFAULT_AUTH_CONFIG_PATH) -> dict:
    if not path.exists():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8"))


def load_microsoft_auth(path: Path = DEFAULT_AUTH_CONFIG_PATH) -> MicrosoftAuthConfig:
    data = _load_auth_data(path).get("microsoft", {})
    client_id = str(data.get("client_id", "")).strip()
    if not client_id or client_id == "00000000-0000-0000-0000-000000000000":
        raise ValueError("Missing microsoft.client_id in config/auth.toml")
    return MicrosoftAuthConfig(client_id=client_id, tenant=str(data.get("tenant", "common")))


def load_google_auth(path: Path = DEFAULT_AUTH_CONFIG_PATH) -> GoogleAuthConfig:
    data = _load_auth_data(path).get("google", {})
    secrets_file = str(data.get("client_secrets_file", "")).strip()
    if not secrets_file:
        raise ValueError("Missing google.client_secrets_file in config/auth.toml")
    resolved = Path(secrets_file)
    if not resolved.is_absolute():
        resolved = PROJECT_ROOT / resolved
    if not resolved.exists():
        raise ValueError(f"Google client secrets file does not exist: {resolved}")
    return GoogleAuthConfig(client_secrets_file=resolved)


def token_path(account_id: str) -> Path:
    TOKEN_DIR.mkdir(mode=0o700, exist_ok=True)
    return TOKEN_DIR / f"{account_id}.json"
