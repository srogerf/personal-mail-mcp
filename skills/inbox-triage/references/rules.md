# Mailbox Triage Rules

Use these as reusable defaults. Current user instructions override these rules.

## Buckets

- `keep`: important records, future commitments, active accounts, bills, payments, tax, legal, medical, reservations, shipments, orders, security alerts, and retained samples.
- `archive`: low-value newsletters, marketing, solicitations, old generic alerts, duplicated samples beyond a retained count, feedback requests, surveys, and completed past-event reminders.
- `review`: new patterns, ambiguous personal mail, unclear business messages, possible action items, and anything where the rule is uncertain.
- `flag`: keep plus visible attention. Use for important tax/legal/security/action-required items when the user wants them highlighted.

## Generic Keep

Keep messages involving tax, bills, payments, invoices, statements, insurance, healthcare, dental, security alerts, login codes, password notices, order confirmations, shipments, refunds, reservations, tickets, appointments, reminders, confirmations, secure email, and action-required notices.

Keep all reservation confirmations and shipment confirmations.

Keep order confirmations in review/flag unless the user creates a narrower rule.

## Generic Archive

Archive feedback requests, surveys, promotions, newsletters, sales, discounts, bonus offers, rewards, travel promos, generic streaming content promos, home-value reports, listing alerts, restaurant promos, generic event promos, old meetup/event digests, and old unflagged messages beyond the user's age threshold.

Archive tickets for past events after the event date has passed.

Archive payment confirmations only when the user has said completed confirmations can be removed, and do not apply that broadly to tax, legal, healthcare, or high-value ambiguous records.

## User-Specific Rules

Do not add personal senders, names, account relationships, or retention preferences to the shared skill. Put those in the user's private rule store, such as:

- `config/mail_rules.local.toml` in the MCP server project
- a private Codex skill copy under `~/.codex/skills`
- a private memory/reference file under `~/.codex/memories`

When a user gives a new durable rule, apply it to the current batch and update the private rule store if the user wants it remembered.

## Appointment Handling

If mail describes a future appointment, reservation, booking, class, webinar, or meeting, propose a calendar entry before archiving. After a calendar entry exists and the user approves, appointment reminder emails may be archived if they are not needed as records.
