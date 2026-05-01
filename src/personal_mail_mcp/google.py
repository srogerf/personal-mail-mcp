from __future__ import annotations

from email.header import decode_header, make_header
import base64

from googleapiclient.discovery import build

from personal_mail_mcp.auth import load_google_credentials
from personal_mail_mcp.config import Account


def list_recent_gmail_messages(account: Account, limit: int = 5) -> list[dict[str, str | None]]:
    service = build("gmail", "v1", credentials=load_google_credentials(account))
    response = (
        service.users()
        .messages()
        .list(userId="me", maxResults=max(1, min(limit, 25)), labelIds=["INBOX"])
        .execute()
    )
    messages = []
    for item in response.get("messages", []):
        message = (
            service.users()
            .messages()
            .get(userId="me", id=item["id"], format="metadata", metadataHeaders=["Subject", "From", "Date"])
            .execute()
        )
        headers = {header["name"].lower(): header["value"] for header in message["payload"].get("headers", [])}
        messages.append(
            {
                "id": message.get("id"),
                "subject": _decode(headers.get("subject")),
                "from": _decode(headers.get("from")),
                "date": headers.get("date"),
            }
        )
    return messages


def list_gmail_messages_query(account: Account, query: str, limit: int = 50) -> list[dict[str, str | None]]:
    service = build("gmail", "v1", credentials=load_google_credentials(account))
    return _list_gmail_messages_query(service, query=query, limit=limit, label_ids=["INBOX"])


def list_gmail_unread_non_inbox_messages(account: Account, limit: int = 100) -> list[dict[str, str | None]]:
    service = build("gmail", "v1", credentials=load_google_credentials(account))
    return _list_gmail_messages_query(service, query="is:unread -in:inbox", limit=limit, label_ids=None)


def _list_gmail_messages_query(service, query: str, limit: int, label_ids: list[str] | None):
    response = (
        service.users()
        .messages()
        .list(userId="me", maxResults=max(1, min(limit, 100)), labelIds=label_ids, q=query)
        .execute()
    )
    messages = []
    for item in response.get("messages", []):
        message = (
            service.users()
            .messages()
            .get(userId="me", id=item["id"], format="metadata", metadataHeaders=["Subject", "From", "Date"])
            .execute()
        )
        headers = {header["name"].lower(): header["value"] for header in message["payload"].get("headers", [])}
        messages.append(
            {
                "id": message.get("id"),
                "subject": _decode(headers.get("subject")),
                "from": _decode(headers.get("from")),
                "date": headers.get("date"),
                "snippet": message.get("snippet"),
            }
        )
    return messages


def list_gmail_inbox_messages(account: Account, limit: int = 100) -> list[dict[str, str | None]]:
    service = build("gmail", "v1", credentials=load_google_credentials(account))
    messages = []
    page_token = None
    while len(messages) < limit:
        response = (
            service.users()
            .messages()
            .list(
                userId="me",
                maxResults=max(1, min(limit - len(messages), 100)),
                labelIds=["INBOX"],
                pageToken=page_token,
            )
            .execute()
        )
        for item in response.get("messages", []):
            message = (
                service.users()
                .messages()
                .get(userId="me", id=item["id"], format="metadata", metadataHeaders=["Subject", "From", "Date"])
                .execute()
            )
            headers = {header["name"].lower(): header["value"] for header in message["payload"].get("headers", [])}
            messages.append(
                {
                    "id": message.get("id"),
                    "subject": _decode(headers.get("subject")),
                    "from": _decode(headers.get("from")),
                    "date": headers.get("date"),
                    "snippet": message.get("snippet"),
                }
            )
            if len(messages) >= limit:
                break
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return messages


def get_gmail_message(account: Account, message_id: str) -> dict[str, str | None]:
    service = build("gmail", "v1", credentials=load_google_credentials(account))
    message = service.users().messages().get(userId="me", id=message_id, format="full").execute()
    headers = {header["name"].lower(): header["value"] for header in message["payload"].get("headers", [])}
    return {
        "id": message.get("id"),
        "subject": _decode(headers.get("subject")),
        "from": _decode(headers.get("from")),
        "date": headers.get("date"),
        "snippet": message.get("snippet"),
        "text": _extract_text(message.get("payload", {})),
    }


def archive_gmail_messages(account: Account, message_ids: list[str]) -> dict[str, int | str]:
    service = build("gmail", "v1", credentials=load_google_credentials(account))
    if not message_ids:
        return {"status": "noop", "archived": 0}
    service.users().messages().batchModify(
        userId="me",
        body={"ids": message_ids, "removeLabelIds": ["INBOX"]},
    ).execute()
    return {"status": "ok", "archived": len(message_ids)}


def _decode(value: str | None) -> str | None:
    if value is None:
        return None
    return str(make_header(decode_header(value)))


def _extract_text(part: dict) -> str:
    chunks = []
    mime_type = part.get("mimeType", "")
    body_data = part.get("body", {}).get("data")
    if body_data and mime_type in {"text/plain", "text/html"}:
        chunks.append(_decode_body(body_data))
    for child in part.get("parts", []) or []:
        chunks.append(_extract_text(child))
    return "\n".join(chunk for chunk in chunks if chunk)


def _decode_body(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8", errors="replace")
