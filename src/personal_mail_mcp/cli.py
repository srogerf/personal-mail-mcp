from __future__ import annotations

import argparse
import json

from personal_mail_mcp.auth import (
    connect_google,
    connect_microsoft,
    connection_status,
)
from personal_mail_mcp.calendar import (
    create_calendar_event,
    delete_calendar_event,
    list_calendar_events,
    update_calendar_event,
)
from personal_mail_mcp.config import get_account, load_accounts
from personal_mail_mcp.google import (
    archive_gmail_messages,
    get_gmail_message,
    list_gmail_inbox_messages,
    list_gmail_messages_query,
    list_recent_gmail_messages,
)
from personal_mail_mcp.mail_audit import archive_plan, audit_mail, unread_non_inbox_scan
from personal_mail_mcp.microsoft import archive_messages, get_message, list_inbox_messages, list_messages_since, list_recent_messages


def main() -> None:
    parser = argparse.ArgumentParser(prog="personal-mail-mcp")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status")

    connect_parser = subparsers.add_parser("connect")
    connect_parser.add_argument("account_id")

    recent_parser = subparsers.add_parser("recent-messages")
    recent_parser.add_argument("account_id")
    recent_parser.add_argument("--limit", type=int, default=5)

    inbox_parser = subparsers.add_parser("inbox")
    inbox_parser.add_argument("account_id")
    inbox_parser.add_argument("--limit", type=int, default=100)

    audit_parser = subparsers.add_parser("audit-mail")
    audit_parser.add_argument("account_ids", nargs="+")
    audit_parser.add_argument("--limit-per-account", type=int, default=250)

    archive_plan_parser = subparsers.add_parser("archive-plan")
    archive_plan_parser.add_argument("account_ids", nargs="+")
    archive_plan_parser.add_argument("--limit-per-account", type=int, default=250)

    missed_parser = subparsers.add_parser("missed-mail")
    missed_parser.add_argument("account_ids", nargs="+")
    missed_parser.add_argument("--limit-per-account", type=int, default=100)

    archive_parser = subparsers.add_parser("archive-mail")
    archive_parser.add_argument("account_id")
    archive_parser.add_argument("message_ids", nargs="+")

    since_parser = subparsers.add_parser("messages-since")
    since_parser.add_argument("account_id")
    since_parser.add_argument("--since", required=True)
    since_parser.add_argument("--limit", type=int, default=50)

    get_message_parser = subparsers.add_parser("message-get")
    get_message_parser.add_argument("account_id")
    get_message_parser.add_argument("message_id")

    gmail_parser = subparsers.add_parser("recent-gmail")
    gmail_parser.add_argument("account_id")
    gmail_parser.add_argument("--limit", type=int, default=5)

    gmail_query_parser = subparsers.add_parser("gmail-query")
    gmail_query_parser.add_argument("account_id")
    gmail_query_parser.add_argument("--query", required=True)
    gmail_query_parser.add_argument("--limit", type=int, default=50)

    gmail_get_parser = subparsers.add_parser("gmail-get")
    gmail_get_parser.add_argument("account_id")
    gmail_get_parser.add_argument("message_id")

    gmail_archive_parser = subparsers.add_parser("gmail-archive")
    gmail_archive_parser.add_argument("account_id")
    gmail_archive_parser.add_argument("message_ids", nargs="+")

    calendar_parser = subparsers.add_parser("calendar-events")
    calendar_parser.add_argument("account_id")
    calendar_parser.add_argument("--start", required=True)
    calendar_parser.add_argument("--end", required=True)
    calendar_parser.add_argument("--limit", type=int, default=25)

    create_event_parser = subparsers.add_parser("create-event")
    create_event_parser.add_argument("account_id")
    create_event_parser.add_argument("--subject", required=True)
    create_event_parser.add_argument("--start", required=True)
    create_event_parser.add_argument("--end", required=True)
    create_event_parser.add_argument("--timezone", default="America/Los_Angeles")
    create_event_parser.add_argument("--body", default="")
    create_event_parser.add_argument("--location", default="")

    delete_event_parser = subparsers.add_parser("delete-event")
    delete_event_parser.add_argument("account_id")
    delete_event_parser.add_argument("event_id")

    update_event_parser = subparsers.add_parser("update-event")
    update_event_parser.add_argument("account_id")
    update_event_parser.add_argument("event_id")
    update_event_parser.add_argument("--subject")
    update_event_parser.add_argument("--body")
    update_event_parser.add_argument("--location")

    args = parser.parse_args()
    if args.command == "status":
        print(json.dumps([connection_status(account) for account in load_accounts()], indent=2))
        return

    if args.command == "connect":
        account = get_account(args.account_id)
        if account.provider == "microsoft":
            result = connect_microsoft(account)
        elif account.provider == "google":
            result = connect_google(account)
        else:
            raise ValueError(f"Unsupported provider for {account.id}: {account.provider}")
        print(json.dumps(result, indent=2))
        return

    if args.command == "recent-messages":
        account = get_account(args.account_id)
        if account.provider != "microsoft":
            raise ValueError(f"recent-messages only supports microsoft accounts for now: {account.id}")
        print(json.dumps(list_recent_messages(account, limit=args.limit), indent=2))
        return

    if args.command == "inbox":
        account = get_account(args.account_id)
        if account.provider == "microsoft":
            messages = list_inbox_messages(account, limit=args.limit)
        elif account.provider == "google":
            messages = list_gmail_inbox_messages(account, limit=args.limit)
        else:
            raise ValueError(f"Unsupported provider for inbox: {account.provider}")
        print(json.dumps(messages, indent=2))
        return

    if args.command == "audit-mail":
        print(json.dumps(audit_mail(args.account_ids, limit_per_account=args.limit_per_account), indent=2))
        return

    if args.command == "archive-plan":
        print(json.dumps(archive_plan(args.account_ids, limit_per_account=args.limit_per_account), indent=2))
        return

    if args.command == "missed-mail":
        print(json.dumps(unread_non_inbox_scan(args.account_ids, limit_per_account=args.limit_per_account), indent=2))
        return

    if args.command == "archive-mail":
        account = get_account(args.account_id)
        if account.provider == "microsoft":
            result = archive_messages(account, args.message_ids)
        elif account.provider == "google":
            result = archive_gmail_messages(account, args.message_ids)
        else:
            raise ValueError(f"Unsupported provider for archive: {account.provider}")
        print(json.dumps(result, indent=2))
        return

    if args.command == "messages-since":
        account = get_account(args.account_id)
        if account.provider != "microsoft":
            raise ValueError(f"messages-since only supports microsoft accounts: {account.id}")
        print(json.dumps(list_messages_since(account, since_iso=args.since, limit=args.limit), indent=2))
        return

    if args.command == "message-get":
        account = get_account(args.account_id)
        if account.provider != "microsoft":
            raise ValueError(f"message-get only supports microsoft accounts: {account.id}")
        print(json.dumps(get_message(account, args.message_id), indent=2))
        return

    if args.command == "recent-gmail":
        account = get_account(args.account_id)
        if account.provider != "google":
            raise ValueError(f"recent-gmail only supports google accounts: {account.id}")
        print(json.dumps(list_recent_gmail_messages(account, limit=args.limit), indent=2))
        return

    if args.command == "gmail-query":
        account = get_account(args.account_id)
        if account.provider != "google":
            raise ValueError(f"gmail-query only supports google accounts: {account.id}")
        print(json.dumps(list_gmail_messages_query(account, query=args.query, limit=args.limit), indent=2))
        return

    if args.command == "gmail-get":
        account = get_account(args.account_id)
        if account.provider != "google":
            raise ValueError(f"gmail-get only supports google accounts: {account.id}")
        print(json.dumps(get_gmail_message(account, args.message_id), indent=2))
        return

    if args.command == "gmail-archive":
        account = get_account(args.account_id)
        if account.provider != "google":
            raise ValueError(f"gmail-archive only supports google accounts: {account.id}")
        print(json.dumps(archive_gmail_messages(account, args.message_ids), indent=2))
        return

    if args.command == "calendar-events":
        account = get_account(args.account_id)
        print(
            json.dumps(
                list_calendar_events(account, start_iso=args.start, end_iso=args.end, limit=args.limit),
                indent=2,
            )
        )
        return

    if args.command == "create-event":
        account = get_account(args.account_id)
        print(
            json.dumps(
                create_calendar_event(
                    account,
                    subject=args.subject,
                    start_iso=args.start,
                    end_iso=args.end,
                    timezone=args.timezone,
                    body=args.body,
                    location=args.location,
                ),
                indent=2,
            )
        )
        return

    if args.command == "delete-event":
        account = get_account(args.account_id)
        print(json.dumps(delete_calendar_event(account, args.event_id), indent=2))
        return

    if args.command == "update-event":
        account = get_account(args.account_id)
        updates = {}
        if args.subject is not None:
            updates["subject"] = args.subject
        if args.body is not None:
            updates["body"] = {"contentType": "text", "content": args.body}
        if args.location is not None:
            updates["location"] = {"displayName": args.location}
        print(json.dumps(update_calendar_event(account, args.event_id, updates), indent=2))
        return


if __name__ == "__main__":
    main()
