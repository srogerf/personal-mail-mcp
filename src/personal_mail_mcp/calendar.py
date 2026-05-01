from __future__ import annotations

from urllib.parse import urlencode

import requests

from personal_mail_mcp.auth import acquire_microsoft_token
from personal_mail_mcp.config import Account
from personal_mail_mcp.microsoft import GRAPH_ROOT


def list_calendar_events(account: Account, start_iso: str, end_iso: str, limit: int = 25) -> list[dict]:
    token = acquire_microsoft_token(account)
    query = urlencode(
        {
            "startDateTime": start_iso,
            "endDateTime": end_iso,
            "$top": max(1, min(limit, 100)),
            "$select": "id,subject,start,end,location,organizer,isCancelled",
            "$orderby": "start/dateTime",
        }
    )
    response = requests.get(
        f"{GRAPH_ROOT}/me/calendarView?{query}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        timeout=20,
    )
    response.raise_for_status()
    return response.json().get("value", [])


def create_calendar_event(
    account: Account,
    subject: str,
    start_iso: str,
    end_iso: str,
    timezone: str = "America/Los_Angeles",
    body: str = "",
    location: str = "",
) -> dict:
    token = acquire_microsoft_token(account)
    payload = {
        "subject": subject,
        "start": {"dateTime": start_iso, "timeZone": timezone},
        "end": {"dateTime": end_iso, "timeZone": timezone},
        "body": {"contentType": "text", "content": body},
        "location": {"displayName": location},
    }
    response = requests.post(
        f"{GRAPH_ROOT}/me/events",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=payload,
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def update_calendar_event(account: Account, event_id: str, updates: dict) -> dict:
    token = acquire_microsoft_token(account)
    response = requests.patch(
        f"{GRAPH_ROOT}/me/events/{event_id}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=updates,
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def delete_calendar_event(account: Account, event_id: str) -> dict[str, str]:
    token = acquire_microsoft_token(account)
    response = requests.delete(
        f"{GRAPH_ROOT}/me/events/{event_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    response.raise_for_status()
    return {"status": "deleted", "event_id": event_id}
