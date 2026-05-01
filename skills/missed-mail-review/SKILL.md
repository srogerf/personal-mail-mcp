---
name: missed-mail-review
description: Review unread messages outside the Inbox, including archived, moved, junk, deleted, or rule-routed mail, and summarize only items that may need attention. Use when the user asks to check missed mail, scan unread archived mail, inspect unread non-inbox messages, find rule-moved items needing attention, or recommend filters for recurring non-inbox noise.
---

# Missed Mail Review

## Workflow

Use this skill for unread messages that are not currently in the Inbox. Use `inbox-triage` for Inbox cleanup.

Start read-only:

1. Identify accounts to inspect. If the user says "all mailboxes," use all configured mail accounts.
2. Run `missed_mail` with a reasonable limit, usually 30-100 unread non-Inbox messages per account.
3. Summarize attention candidates by account, folder, sender, subject, and reason.
4. Suppress obvious archive/noise details unless the user asks for counts or examples.
5. Recommend filters or unsubscribe candidates for recurring non-Inbox noise.

## Attention Criteria

Prioritize unread non-Inbox messages that are financial, legal, medical, tax-related, security-related, order/shipment/reservation-related, appointment-related, personal, or otherwise ambiguous.

Treat old marketing, newsletters, sale mail, generic travel promos, surveys, and repeated low-value senders as noise unless the user has a rule to keep them.

## Filter Recommendations

Recommend a filter when the same noise pattern appears multiple times, appears across accounts, or is repeatedly unread outside the Inbox. Include the sender/pattern, affected account ids, and suggested action such as archive, move to a folder, or unsubscribe.

Do not create remote provider rules unless the user explicitly requests it and the required OAuth scopes are configured:

- Microsoft/Exchange message rules: `MailboxSettings.ReadWrite`
- Gmail filters: `gmail.settings.basic`

## Output

Keep output concise:

```text
Missed Mail
- <account>: <count> attention candidates
- <folder>: <sender>, "<subject>" - <reason>

Filter / Unsubscribe Ideas
- Filter: <pattern> -> <action>
- Unsubscribe: <sender> -> <reason>
```

Do not quote long email bodies.
