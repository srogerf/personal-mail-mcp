---
name: email-appointment-harvest
description: Scan connected email accounts for appointment confirmations, reminders, bookings, invitations, and date/time commitments, then propose calendar entries for user approval before creating or updating Exchange/Outlook calendar events. Use when the user asks to review recent email for appointments, add missed appointments from email, harvest calendar items from mail, or repeat the 7-day email-to-calendar workflow.
---

# Email Appointment Harvest

## Overview

Use this skill to convert recent email into approved calendar entries. The default workflow is read-only scanning first, concise proposal second, and calendar writes only after explicit approval.

The local integration is `personal-mail-mcp` at `<repo-path>` as documented by the project README. Prefer the MCP tools when available; use the CLI only when MCP tools are not loaded or when a quick local helper is needed.

## Default Scope

- Scan the last seven days unless the user gives a different range.
- Scan all configured accounts unless the user narrows the accounts.
- Treat the Exchange calendar account as the write target unless the user specifies another calendar.
- Never create, update, or delete calendar entries until the user approves specific proposed entries.

## Workflow

1. List configured accounts and confirm the calendar-owning account if unclear.
2. Pull message summaries for the date range across Exchange and Gmail accounts.
3. Identify appointment candidates: confirmations, reminders, bookings, classes, medical/dental, financial calls, travel, reservations, service windows, or event invitations.
4. Filter out likely marketing unless there is a clear user commitment or reservation.
5. For each candidate, fetch the full source email before proposing or creating the event.
6. Extract structured fields:
   - appointment/title
   - date and time with timezone
   - location
   - staff/provider/host
   - phone/email/contact details
   - price/payment note
   - preparation note
   - cancellation/reschedule policy
   - source sender, subject, and received date
7. Check the target calendar for existing events in the relevant windows.
8. Present proposed entries with confidence and any ambiguity.
9. After approval, create only missing entries or update existing entries as requested.
10. Summarize what changed and what was ignored.

## Proposal Format

Keep proposals compact:

```text
A. <title>
Time: <date/time/timezone>
Location: <location or unknown>
Source: <sender>, "<subject>"
Notes: <important context>
Confidence: high|medium|low
```

Ask the user to approve or deny by letter. Do not create entries from low-confidence candidates without clarifying the ambiguity.

## Calendar Note Pattern

Use structured plain-text notes on created/updated entries:

```text
Source: <source email sender/role>.

Appointment: <appointment name>
Date/time: <date and local time>
Location: <address or location>
Staff/provider: <person or organization>
Phone: <phone if present>
Email: <email if present>
Price/payment: <payment detail if present>

Preparation note: <prep detail if present>
Confirmation note: <confirmation detail if present>
Cancellation note: <policy if present>
Reschedule note: <reschedule detail if present>

Source email: <sender>, subject '<subject>', received <date>.
```

Omit fields that are not present. Do not invent missing information.

## Duplicate Checks

Before creating an event, query the calendar for the candidate date. Treat an event as probably existing when the title, time, and provider are close enough. If an existing event lacks structured notes or location, prefer updating it after approval rather than creating a duplicate.

## Safety Rules

- Do not add marketing events unless the user explicitly approves them.
- Do not add past events unless the user explicitly approves historical entries.
- Do not expose long private email bodies in the final answer; summarize only what matters for approval.
- Do not include unnecessary personal identifiers in notes when a shorter contact/context field is enough.
- Do not perform destructive mail actions as part of this skill.

## Useful Commands

Use these if direct MCP tools are not available:

```bash
cd <repo-path>
.venv/bin/python -m personal_mail_mcp.cli status
.venv/bin/python -m personal_mail_mcp.cli messages-since <exchange-account> --since <ISO-UTC> --limit 100
.venv/bin/python -m personal_mail_mcp.cli gmail-query <gmail-account> --query 'newer:YYYY/M/D' --limit 100
.venv/bin/python -m personal_mail_mcp.cli message-get <exchange-account> <message-id>
.venv/bin/python -m personal_mail_mcp.cli gmail-get <gmail-account> <message-id>
.venv/bin/python -m personal_mail_mcp.cli calendar-events <calendar-account> --start <ISO> --end <ISO>
.venv/bin/python -m personal_mail_mcp.cli create-event <calendar-account> --subject ... --start ... --end ... --timezone ...
.venv/bin/python -m personal_mail_mcp.cli update-event <calendar-account> <event-id> --location ... --body ...
```

