from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from personal_mail_mcp.calendar import (
    create_calendar_event,
    delete_calendar_event,
    list_calendar_events,
    update_calendar_event,
)
from personal_mail_mcp.config import get_account, load_accounts
from personal_mail_mcp.google import archive_gmail_messages, list_gmail_inbox_messages, list_recent_gmail_messages
from personal_mail_mcp.mail_audit import archive_plan, audit_mail, unread_non_inbox_scan
from personal_mail_mcp.microsoft import archive_messages as archive_microsoft_messages
from personal_mail_mcp.microsoft import list_inbox_messages, list_recent_messages


mcp = FastMCP("personal-mail")


@mcp.tool()
def list_accounts() -> list[dict[str, str | bool]]:
    """List configured mail/calendar accounts without exposing secrets."""
    return [
        {
            "id": account.id,
            "provider": account.provider,
            "email": account.email,
            "calendar": account.calendar,
        }
        for account in load_accounts()
    ]


@mcp.tool()
def health_check() -> dict[str, str | int]:
    """Return basic server status."""
    return {
        "status": "ok",
        "configured_accounts": len(load_accounts()),
    }


@mcp.tool()
def microsoft_recent_messages(account_id: str, limit: int = 5) -> list[dict[str, str | bool | None]]:
    """List recent Microsoft mailbox messages for a configured account."""
    account = get_account(account_id)
    if account.provider != "microsoft":
        raise ValueError(f"Account is not a Microsoft account: {account_id}")
    return list_recent_messages(account, limit=limit)


@mcp.tool()
def gmail_recent_messages(account_id: str, limit: int = 5) -> list[dict[str, str | None]]:
    """List recent Gmail inbox messages for a configured account."""
    account = get_account(account_id)
    if account.provider != "google":
        raise ValueError(f"Account is not a Google account: {account_id}")
    return list_recent_gmail_messages(account, limit=limit)


@mcp.tool()
def mail_inbox(account_id: str, limit: int = 100) -> list[dict]:
    """List inbox messages for a configured Microsoft or Gmail account."""
    account = get_account(account_id)
    if account.provider == "microsoft":
        return list_inbox_messages(account, limit=limit)
    if account.provider == "google":
        return list_gmail_inbox_messages(account, limit=limit)
    raise ValueError(f"Unsupported provider for inbox: {account.provider}")


@mcp.tool()
def mail_audit(account_ids: list[str], limit_per_account: int = 250) -> dict:
    """Classify inbox mail into keep, flag, archive, and review buckets."""
    return audit_mail(account_ids, limit_per_account=limit_per_account)


@mcp.tool()
def mail_archive_plan(account_ids: list[str], limit_per_account: int = 250) -> dict:
    """Dry-run archive candidates grouped by account and reason with message ids and subjects."""
    return archive_plan(account_ids, limit_per_account=limit_per_account)


@mcp.tool()
def missed_mail(account_ids: list[str], limit_per_account: int = 100) -> dict:
    """List unread messages outside the inbox that may need attention."""
    return unread_non_inbox_scan(account_ids, limit_per_account=limit_per_account)


@mcp.tool()
def archive_messages(account_id: str, message_ids: list[str]) -> dict[str, int | str]:
    """Archive specific messages by id without deleting them."""
    account = get_account(account_id)
    if account.provider == "microsoft":
        return archive_microsoft_messages(account, message_ids)
    if account.provider == "google":
        return archive_gmail_messages(account, message_ids)
    raise ValueError(f"Unsupported provider for archive: {account.provider}")


@mcp.tool()
def microsoft_calendar_events(
    account_id: str, start_iso: str, end_iso: str, limit: int = 25
) -> list[dict]:
    """List Microsoft calendar events between two ISO timestamps."""
    account = get_account(account_id)
    if account.provider != "microsoft":
        raise ValueError(f"Account is not a Microsoft account: {account_id}")
    return list_calendar_events(account, start_iso=start_iso, end_iso=end_iso, limit=limit)


@mcp.tool()
def microsoft_create_calendar_event(
    account_id: str,
    subject: str,
    start_iso: str,
    end_iso: str,
    timezone: str = "America/Los_Angeles",
    body: str = "",
    location: str = "",
) -> dict:
    """Create a Microsoft calendar event."""
    account = get_account(account_id)
    if account.provider != "microsoft":
        raise ValueError(f"Account is not a Microsoft account: {account_id}")
    return create_calendar_event(account, subject, start_iso, end_iso, timezone, body, location)


@mcp.tool()
def microsoft_update_calendar_event(account_id: str, event_id: str, updates: dict) -> dict:
    """Update a Microsoft calendar event using a Graph event patch payload."""
    account = get_account(account_id)
    if account.provider != "microsoft":
        raise ValueError(f"Account is not a Microsoft account: {account_id}")
    return update_calendar_event(account, event_id, updates)


@mcp.tool()
def microsoft_delete_calendar_event(account_id: str, event_id: str) -> dict[str, str]:
    """Delete a Microsoft calendar event by id."""
    account = get_account(account_id)
    if account.provider != "microsoft":
        raise ValueError(f"Account is not a Microsoft account: {account_id}")
    return delete_calendar_event(account, event_id)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
