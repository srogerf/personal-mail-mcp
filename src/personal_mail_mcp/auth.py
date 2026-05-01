from __future__ import annotations

from pathlib import Path

import msal
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from personal_mail_mcp.config import (
    Account,
    load_google_auth,
    load_microsoft_auth,
    token_path,
)


MICROSOFT_SCOPES = [
    "https://graph.microsoft.com/Mail.Read",
    "https://graph.microsoft.com/Mail.ReadWrite",
    "https://graph.microsoft.com/Calendars.ReadWrite",
]

GOOGLE_SCOPES = [
  "https://www.googleapis.com/auth/gmail.readonly",
  "https://www.googleapis.com/auth/gmail.modify",
]


def connection_status(account: Account) -> dict[str, str | bool]:
    path = token_path(account.id)
    return {
        "id": account.id,
        "provider": account.provider,
        "email": account.email,
        "token_cached": path.exists(),
        "token_path": str(path),
    }


def connect_microsoft(account: Account) -> dict[str, str | bool]:
    auth = load_microsoft_auth()
    cache = msal.SerializableTokenCache()
    path = token_path(account.id)
    if path.exists():
        cache.deserialize(path.read_text(encoding="utf-8"))

    app = msal.PublicClientApplication(
        auth.client_id,
        authority=f"https://login.microsoftonline.com/{auth.tenant}",
        token_cache=cache,
    )
    flow = app.initiate_device_flow(scopes=MICROSOFT_SCOPES)
    if "user_code" not in flow:
        raise RuntimeError(f"Microsoft device flow failed: {flow}")

    print(flow["message"], flush=True)
    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        raise RuntimeError(f"Microsoft token acquisition failed: {result}")

    _write_private(path, cache.serialize())
    return {"id": account.id, "provider": account.provider, "connected": True}


def acquire_microsoft_token(account: Account) -> str:
    auth = load_microsoft_auth()
    path = token_path(account.id)
    if not path.exists():
        raise RuntimeError(f"No cached Microsoft token for account: {account.id}")

    cache = msal.SerializableTokenCache()
    cache.deserialize(path.read_text(encoding="utf-8"))
    app = msal.PublicClientApplication(
        auth.client_id,
        authority=f"https://login.microsoftonline.com/{auth.tenant}",
        token_cache=cache,
    )
    accounts = app.get_accounts(username=account.email)
    if not accounts:
        accounts = app.get_accounts()
    result = app.acquire_token_silent(MICROSOFT_SCOPES, account=accounts[0] if accounts else None)
    if not result or "access_token" not in result:
        raise RuntimeError(f"Could not refresh Microsoft token for account: {account.id}")

    if cache.has_state_changed:
        _write_private(path, cache.serialize())
    return str(result["access_token"])


def connect_google(account: Account) -> dict[str, str | bool]:
    auth = load_google_auth()
    flow = InstalledAppFlow.from_client_secrets_file(str(auth.client_secrets_file), GOOGLE_SCOPES)
    creds = flow.run_local_server(host="127.0.0.1", port=0, open_browser=False)
    path = token_path(account.id)
    _write_private(path, creds.to_json())
    return {"id": account.id, "provider": account.provider, "connected": True}


def load_google_credentials(account: Account) -> Credentials:
    return Credentials.from_authorized_user_file(str(token_path(account.id)), GOOGLE_SCOPES)


def _write_private(path: Path, content: str) -> None:
    path.parent.mkdir(mode=0o700, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(0o600)
