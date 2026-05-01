---
name: review-all-mail
description: Run the full personal mail review workflow by combining email appointment harvesting, Inbox triage, and missed-mail review. Use when the user asks for a regular mail review, daily/weekly email check, calendar-and-inbox workflow, all-mail cleanup report, moved-mail report, filter recommendations, unsubscribe recommendations, or a complete review of Inbox plus unread non-Inbox mail.
---

# Review All Mail

## Overview

Use this skill to orchestrate three focused skills into one report-driven workflow:

1. `email-appointment-harvest`: check recent mail for calendar items.
2. `inbox-triage`: triage Inbox archive candidates.
3. `missed-mail-review`: check unread messages outside the Inbox for missed attention items.

## Default Scope

- Accounts: all configured accounts unless the user narrows scope.
- Mail scan window: last seven days for calendar harvesting unless the user specifies otherwise.
- Inbox triage depth: 100-250 messages per account.
- Missed-mail depth: 30-100 unread non-Inbox messages per account.
- Calendar target: the configured calendar-owning Exchange account unless specified otherwise.

## Workflow

1. List or infer configured accounts and the calendar account.
2. Use `email-appointment-harvest` behavior first. Do not archive appointment source emails until needed calendar entries exist or the user says they are safe to archive.
3. Use `inbox-triage` behavior next. Run `mail_archive_plan`, summarize grouped Inbox archive candidates, and review `filter_recommendations`.
4. If the user asks to apply the Inbox archive plan, call `archive_messages` by account with exact ids from the plan.
5. Use `missed-mail-review` behavior last. Run `missed_mail` and summarize unread non-Inbox attention candidates by account, folder, and reason.
6. Recommend filters for repeated noise patterns and unsubscribes for sources the user does not follow.
7. Produce the final report.

## Report Format

Keep the report concise:

```text
Calendar
- Proposed: <count>; Created/updated: <count>; Needs approval: <summary>

Inbox Triage
- Archived/moved: <count by account>
- Not moved: <notable review/keep items>

Missed Mail
- Attention candidates outside Inbox: <count by account>
- Notable items: <subject/source/folder>

Filter / Unsubscribe Recommendations
- Filter: <sender/pattern> -> <suggested action and accounts>
- Unsubscribe: <sender> -> <reason>
```

When messages are moved, include exact subjects and counts. Avoid long email body excerpts.

## Safety

Never delete mail. Do not move ambiguous financial, legal, medical, tax, security, appointment, order, reservation, or personal messages unless the user explicitly instructs it.

Do not unsubscribe automatically. Recommend unsubscribe candidates for recurring marketing/newsletter noise the user does not follow, then wait for user direction.
