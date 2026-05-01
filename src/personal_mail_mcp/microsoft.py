from __future__ import annotations

from urllib.parse import urlencode

import requests

from personal_mail_mcp.auth import acquire_microsoft_token
from personal_mail_mcp.config import Account


GRAPH_ROOT = "https://graph.microsoft.com/v1.0"


def list_recent_messages(account: Account, limit: int = 5) -> list[dict[str, str | bool | None]]:
    token = acquire_microsoft_token(account)
    query = urlencode(
        {
            "$top": max(1, min(limit, 25)),
            "$select": "id,subject,from,receivedDateTime,isRead",
            "$orderby": "receivedDateTime desc",
        }
    )
    response = requests.get(
        f"{GRAPH_ROOT}/me/messages?{query}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        timeout=20,
    )
    response.raise_for_status()
    messages = []
    for item in response.json().get("value", []):
        sender = item.get("from", {}).get("emailAddress", {})
        messages.append(
            {
                "id": item.get("id"),
                "subject": item.get("subject"),
                "from_name": sender.get("name"),
                "from_address": sender.get("address"),
                "received": item.get("receivedDateTime"),
                "is_read": item.get("isRead"),
            }
        )
    return messages


def list_inbox_messages(account: Account, limit: int = 100) -> list[dict[str, str | bool | None]]:
    token = acquire_microsoft_token(account)
    page_size = max(1, min(limit, 100))
    query = urlencode(
        {
            "$top": page_size,
            "$select": "id,subject,from,receivedDateTime,isRead,bodyPreview",
            "$orderby": "receivedDateTime desc",
        }
    )
    url = f"{GRAPH_ROOT}/me/mailFolders/inbox/messages?{query}"
    messages = []
    while url and len(messages) < limit:
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        for item in payload.get("value", []):
            if len(messages) >= limit:
                break
            messages.append(_message_summary(item))
        url = payload.get("@odata.nextLink")
    return messages


def list_unread_non_inbox_messages(
    account: Account, limit: int = 100
) -> list[dict[str, str | bool | None]]:
    token = acquire_microsoft_token(account)
    folders = _mail_folder_names(token)
    inbox_id = next((folder_id for folder_id, name in folders.items() if name.lower() == "inbox"), "")
    query = urlencode(
        {
            "$top": max(1, min(limit, 100)),
            "$select": "id,subject,from,receivedDateTime,isRead,bodyPreview,parentFolderId",
            "$orderby": "receivedDateTime desc",
            "$filter": "isRead eq false",
        }
    )
    response = requests.get(
        f"{GRAPH_ROOT}/me/messages?{query}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        timeout=20,
    )
    response.raise_for_status()
    messages = []
    for item in response.json().get("value", []):
        parent_folder_id = str(item.get("parentFolderId") or "")
        if parent_folder_id == inbox_id:
            continue
        messages.append(
            {
                **_message_summary(item),
                "folder_id": parent_folder_id,
                "folder": folders.get(parent_folder_id, parent_folder_id),
            }
        )
        if len(messages) >= limit:
            break
    return messages


def archive_messages(account: Account, message_ids: list[str]) -> dict[str, int | str]:
    token = acquire_microsoft_token(account)
    if not message_ids:
        return {"status": "noop", "archived": 0}
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    archived = 0
    for message_id in message_ids:
        response = requests.post(
            f"{GRAPH_ROOT}/me/messages/{message_id}/move",
            headers=headers,
            json={"destinationId": "archive"},
            timeout=20,
        )
        response.raise_for_status()
        archived += 1
    return {"status": "ok", "archived": archived}


def list_messages_since(account: Account, since_iso: str, limit: int = 50) -> list[dict[str, str | bool | None]]:
    token = acquire_microsoft_token(account)
    query = urlencode(
        {
            "$top": max(1, min(limit, 100)),
            "$select": "id,subject,from,receivedDateTime,isRead,bodyPreview",
            "$orderby": "receivedDateTime desc",
            "$filter": f"receivedDateTime ge {since_iso}",
        }
    )
    response = requests.get(
        f"{GRAPH_ROOT}/me/messages?{query}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        timeout=20,
    )
    response.raise_for_status()
    messages = []
    for item in response.json().get("value", []):
        sender = item.get("from", {}).get("emailAddress", {})
        messages.append(
            {
                "id": item.get("id"),
                "subject": item.get("subject"),
                "from_name": sender.get("name"),
                "from_address": sender.get("address"),
                "received": item.get("receivedDateTime"),
                "is_read": item.get("isRead"),
                "preview": item.get("bodyPreview"),
            }
        )
    return messages


def get_message(account: Account, message_id: str) -> dict[str, str | bool | None]:
    token = acquire_microsoft_token(account)
    response = requests.get(
        f"{GRAPH_ROOT}/me/messages/{message_id}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        params={"$select": "id,subject,from,receivedDateTime,isRead,body,bodyPreview"},
        timeout=20,
    )
    response.raise_for_status()
    item = response.json()
    sender = item.get("from", {}).get("emailAddress", {})
    return {
        "id": item.get("id"),
        "subject": item.get("subject"),
        "from_name": sender.get("name"),
        "from_address": sender.get("address"),
        "received": item.get("receivedDateTime"),
        "is_read": item.get("isRead"),
        "preview": item.get("bodyPreview"),
        "body_content_type": item.get("body", {}).get("contentType"),
        "body": item.get("body", {}).get("content"),
    }


def _message_summary(item: dict) -> dict[str, str | bool | None]:
    sender = item.get("from", {}).get("emailAddress", {})
    return {
        "id": item.get("id"),
        "subject": item.get("subject"),
        "from_name": sender.get("name"),
        "from_address": sender.get("address"),
        "received": item.get("receivedDateTime"),
        "is_read": item.get("isRead"),
        "preview": item.get("bodyPreview"),
    }


def _mail_folder_names(token: str) -> dict[str, str]:
    response = requests.get(
        f"{GRAPH_ROOT}/me/mailFolders",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        params={"$top": 100, "$select": "id,displayName"},
        timeout=20,
    )
    response.raise_for_status()
    return {
        str(item.get("id") or ""): str(item.get("displayName") or "")
        for item in response.json().get("value", [])
    }
