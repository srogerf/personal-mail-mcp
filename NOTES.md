# Notes

## Improvement Backlog

- Expand tests for `mail_audit.py`: local override loading, provider normalization, and edge cases around age-based rules.
- Make `flag` a real provider operation for Outlook and Gmail, rather than only a classifier bucket.
- Add an `apply-archive-plan` helper that accepts a dry-run plan JSON and archives ids grouped by account.
- Add provider-specific rule creation helpers for recurring filter recommendations, starting with Outlook move/archive rules.
- Add OAuth setup/docs for Microsoft `MailboxSettings.ReadWrite` and Gmail `gmail.settings.basic` before enabling remote filter creation.
- Add a write-action guard for calendar delete/update and archive operations, such as a CLI `--yes` flag or MCP two-step plan/apply convention.
- Split provider clients into shared helpers for pagination, retries, response handling, and message normalization.
- Add rule schema validation for `config/mail_rules*.toml` with clear errors for malformed rules.
- Add tests for Microsoft/Gmail client normalization using mocked provider responses.
- Add tests for CLI command wiring with mocked account/provider calls.
- Clean generated local artifacts before sharing, especially `__pycache__/` and `src/personal_mail_mcp.egg-info/`.

## Privacy / Reuse

- Keep reusable defaults in `config/mail_rules.default.toml`.
- Keep personal sender rules and retention preferences in ignored `config/mail_rules.local.toml`.
- Keep shared skills generic; put personal rules in local config or private Codex skill copies.
