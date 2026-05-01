---
name: inbox-triage
description: Triage Inbox messages into keep, archive, review, and flag buckets using local MCP mail tools and user-approved mailbox rules. Use when the user asks Codex to audit an inbox, clean up inbox mail, summarize Inbox archive candidates, find Inbox noise, apply Inbox retention rules, dry-run archive candidates, or move low-value Inbox messages by exact id.
---

# Inbox Triage

## Workflow

Use this skill only for messages currently in the Inbox. Use `missed-mail-review` for unread messages outside the Inbox.

Prefer `mail_archive_plan` for routine Inbox cleanup because it is read-only and returns exact message ids grouped by account and archive reason. Use `mail_audit` when the user wants the full keep/archive/review/flag breakdown, `mail_inbox` for account-specific inspection, and `archive_messages` only with exact message ids from the plan or a direct user instruction.

Start read-only:

1. Identify accounts to inspect. If the user says "all inboxes," use all configured mail accounts.
2. Run `mail_archive_plan` with enough depth for the request, usually 100-250 Inbox messages per account.
3. Show the grouped archive plan with account id, reason, message id, subject, sender, and received date.
4. If the user asks to apply the plan, call `archive_messages` with the exact ids from the plan.
5. Summarize what changed and what remains for review.

## Safety

Never delete mail. Archive means remove from Inbox or move to Archive while preserving the message. Do not move messages from a new, ambiguous, financial, medical, tax-related, legal, personal, appointment-related, or potentially actionable pattern unless the dry-run plan makes the action clear or the user directs the move.

Keep future appointment, reservation, ticket, bill, payment, tax, security, healthcare, HOA, shipment, order, refund, and account-access messages unless a stronger user rule says otherwise. If a mail item looks like a future appointment, mention it and do not archive it until any needed calendar entry exists and the user approves.

## Rules

For detailed retention and classification rules, read `references/rules.md` when running an Inbox cleanup or when explaining why a message belongs in a bucket.

If a user changes a rule during triage, apply it to the current batch and consider updating the MCP server's deterministic rules if the pattern should persist across future audits.

## Output

Keep output concise. For archive plans, group by account and reason and list id plus subject. For completed action, report counts and the exact subjects moved.
