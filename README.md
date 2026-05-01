# personal-mail-mcp

Local MCP server for Codex access to personal mail and calendar accounts.

Current target:

- GoDaddy-hosted Exchange mailboxes and calendar through Microsoft Graph.
- Gmail through Google APIs.
- Read-only audit/plan tools plus explicit archive and calendar-write tools.

No OAuth secrets or token caches should be committed. Copy
`config/accounts.example.toml` to `config/accounts.toml` for local settings.
Copy `config/auth.example.toml` to `config/auth.toml` for OAuth app settings.
Keep local config files private to your user account.

Recommended permissions for local-only files:

```bash
chmod 700 .private .tokens
chmod 600 config/accounts.toml config/auth.toml config/mail_rules.local.toml
```

## Local project setup

Create and install the local environment:

```bash
cd <repo-path>
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[providers]'
```

## Codex config

Add the MCP server to `~/.codex/config.toml`:

```toml
[mcp_servers.personal_mail]
type = "stdio"
command = "<repo-path>/.venv/bin/python"
args = ["-m", "personal_mail_mcp.server"]
startup_timeout_sec = 30
```

Restart Codex after changing the config so the MCP server appears in the active
tool list.

## Account config

Create `config/accounts.toml`:

```toml
[[accounts]]
id = "exchange_primary"
provider = "microsoft"
email = "primary@example.com"
calendar = true

[[accounts]]
id = "exchange_secondary"
provider = "microsoft"
email = "secondary@example.com"
calendar = false

[[accounts]]
id = "google_primary"
provider = "google"
email = "public-example@gmail.com"
calendar = false
```

This file is ignored by git.

## Microsoft app registration

The GoDaddy accounts are Exchange Online accounts reachable through Microsoft
Graph. No GoDaddy-specific API is needed.

1. Open the Microsoft Entra admin center:

   ```text
   https://entra.microsoft.com/
   ```

2. Go to:

   ```text
   Entra ID > App registrations > New registration
   ```

   If the left navigation is different, search for `App registrations` in the
   portal search box.

3. Register the app:

   ```text
   Name: personal-mail-mcp
   Supported account types: Single tenant only - your Microsoft 365 tenant
   ```

4. On the app registration Overview page, copy:

   ```text
   Application (client) ID
   Directory (tenant) ID
   ```

5. Under Authentication, add a redirect URL for a native/local app:

   ```text
   http://localhost
   ```

   This appears under Mobile and desktop applications / Redirect URLs in the
   current portal UI.

6. Under Authentication settings, enable public/native client flows. The portal
   wording may be one of:

   ```text
   Allow public client flows
   Enable the following mobile and desktop flows
   Treat application as a public client
   ```

   Set it to `Yes` and save.

7. Under API permissions, add Microsoft Graph delegated permissions:

   ```text
   Mail.Read
   Mail.ReadWrite
   Calendars.ReadWrite
   offline_access
   ```

Create `config/auth.toml` with the copied IDs:

```toml
[microsoft]
client_id = "APPLICATION_CLIENT_ID_FROM_ENTRA"
tenant = "DIRECTORY_TENANT_ID_FROM_ENTRA"

[google]
client_secrets_file = ".private/google-oauth-client.json"
```

Do not put OpenAI, ChatGPT, Codex, or GitHub tokens in this file. This file is
ignored by git.

## Connect Exchange Online accounts

```bash
cd <repo-path>
.venv/bin/python -m personal_mail_mcp.cli status
PYTHONUNBUFFERED=1 .venv/bin/python -m personal_mail_mcp.cli connect exchange_primary
PYTHONUNBUFFERED=1 .venv/bin/python -m personal_mail_mcp.cli connect exchange_secondary
```

Each connect command prints a Microsoft device-code URL and code. Open the URL,
enter the code, and sign in with the matching account:

```text
exchange_primary   -> primary Exchange Online mailbox
exchange_secondary -> secondary Exchange Online mailbox
```

Successful connections write local token cache files under `.tokens/`, which is
ignored by git.

Verify:

```bash
.venv/bin/python -m personal_mail_mcp.cli status
```

The Microsoft accounts should show:

```text
token_cached: true
```

## Read-only verification

Fetch the latest five message subjects from the main Exchange mailbox:

```bash
.venv/bin/python -m personal_mail_mcp.cli recent-messages exchange_primary --limit 5
```

The equivalent MCP tool exposed to Codex is:

```text
microsoft_recent_messages(account_id, limit=5)
```

## Gmail setup

Use a Google Cloud project for the Gmail API and OAuth desktop credentials.

1. Open Google Cloud Console:

   ```text
   https://console.cloud.google.com/
   ```

2. Create or select a project, then enable:

   ```text
   Gmail API
   ```

3. Configure OAuth consent under:

   ```text
   Google Auth Platform > Branding
   ```

   Use a simple app name such as `personal-mail-mcp`. For personal Gmail
   accounts, use `External` audience and add your Gmail address as a test user
   under:

   ```text
   Google Auth Platform > Audience > Test users
   ```

4. Create a desktop OAuth client under:

   ```text
   Google Auth Platform > Clients > Create client
   ```

   Use:

   ```text
   Application type: Desktop app
   Name: personal-mail-mcp
   ```

5. Download the OAuth client JSON and store it locally:

   ```text
   <repo-path>/.private/google-oauth-client.json
   ```

   Tighten permissions:

   ```bash
   chmod 600 .private/google-oauth-client.json
   ```

6. Ensure `config/auth.toml` points to the file:

   ```toml
   [google]
   client_secrets_file = ".private/google-oauth-client.json"
   ```

7. Connect the Gmail account:

   ```bash
   cd <repo-path>
   PYTHONUNBUFFERED=1 .venv/bin/python -m personal_mail_mcp.cli connect google_primary
   ```

   Open the printed Google URL, sign in with the configured test user, and
   approve the Gmail read/modify scopes.

8. Verify:

   ```bash
   .venv/bin/python -m personal_mail_mcp.cli status
   ```

   The Gmail account should show:

   ```text
   token_cached: true
   ```

Fetch the latest three Gmail inbox subjects:

```bash
.venv/bin/python -m personal_mail_mcp.cli recent-gmail google_primary --limit 3
```

The equivalent MCP tool exposed to Codex is:

```text
gmail_recent_messages(account_id, limit=5)
```

## Mail triage

The MCP server includes reusable inbox audit and archive helpers so repeated
triage does not require ad hoc scripts.

Run a read-only audit across accounts:

```bash
cd <repo-path>
.venv/bin/python -m personal_mail_mcp.cli audit-mail exchange_primary exchange_secondary google_primary --limit-per-account 250
```

Create a dry-run archive plan. This returns only archive candidates grouped
across all requested accounts by archive reason, sender, and normalized subject.
Each message includes its account id, message id, subject, sender, and received
date:

```bash
.venv/bin/python -m personal_mail_mcp.cli archive-plan exchange_primary exchange_secondary google_primary --limit-per-account 250
```

List a single inbox with pagination:

```bash
.venv/bin/python -m personal_mail_mcp.cli inbox exchange_primary --limit 100
```

Scan for unread mail outside the Inbox, such as archived or rule-moved
messages. The command classifies those messages and returns attention
candidates separately from obvious archive/noise:

```bash
.venv/bin/python -m personal_mail_mcp.cli missed-mail exchange_primary exchange_secondary google_primary --limit-per-account 100
```

Archive selected messages by id:

```bash
.venv/bin/python -m personal_mail_mcp.cli archive-mail exchange_primary <message-id> [<message-id> ...]
```

The equivalent MCP tools exposed to Codex are:

```text
mail_inbox(account_id, limit=100)
mail_audit(account_ids, limit_per_account=250)
mail_archive_plan(account_ids, limit_per_account=250)
missed_mail(account_ids, limit_per_account=100)
archive_messages(account_id, message_ids)
```

The audit classifier is intentionally deterministic. It groups mail into
`keep`, `flag`, `archive`, and `review`. Use `mail_archive_plan` as the normal
review step before moving messages; it is read-only and contains the exact ids
needed for `archive_messages`. When the same archive pattern appears more than
once or across multiple accounts, the plan also returns filter recommendations
that can be used to create mailbox/provider rules for future messages.

Remote filter/rule creation is possible but requires additional OAuth scopes:
Microsoft Graph message rules require `MailboxSettings.ReadWrite`; Gmail filter
creation requires `gmail.settings.basic`. Until those are added and approved,
the server should only recommend filters rather than creating them.

Reusable defaults live in `config/mail_rules.default.toml`. User-specific
senders, retention counts, and archive patterns belong in
`config/mail_rules.local.toml`, which is ignored by git. Use
`config/mail_rules.example.toml` as a template for local overrides.

## Optional Codex skill

This project includes a shareable Codex skill:

```text
skills/email-appointment-harvest
skills/inbox-triage
skills/missed-mail-review
skills/review-all-mail
```

The skill documents the repeatable workflow for scanning recent email,
proposing appointment/calendar candidates, waiting for approval, and then
creating or updating only approved calendar entries.

Install it into a Codex environment:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/email-appointment-harvest "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -R skills/inbox-triage "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -R skills/missed-mail-review "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -R skills/review-all-mail "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Restart Codex after installing. Example request:

```text
Use email appointment harvest to scan the last 7 days of email for appointments,
propose calendar entries, and add only the entries I approve.
```

The installed skill assumes this MCP server is configured in Codex and that the
mail/calendar OAuth tokens have already been connected.

## Security notes

- `config/auth.toml`, `config/accounts.toml`, and `.tokens/` are local-only.
- The Microsoft app is a public/native client; do not create or store a client
  secret for this CLI flow.
- Gmail client credentials under `.private/` and token caches under `.tokens/`
  should be mode `600` for files and `700` for directories.
- Microsoft `Mail.ReadWrite`, Google `gmail.modify`, and Microsoft
  `Calendars.ReadWrite` are required for the current archive/calendar tools.
  Keep the app registration scoped to only the delegated permissions you use.
- Treat `archive_messages` and calendar mutation tools as write actions. Prefer
  `mail_archive_plan` and calendar reads before applying changes.
- Rotate any personal access tokens that were ever stored in plaintext config.
