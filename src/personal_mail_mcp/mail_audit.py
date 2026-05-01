from __future__ import annotations

from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from pathlib import Path
import re
import tomllib

from personal_mail_mcp.config import DEFAULT_MAIL_RULES_PATH, LOCAL_MAIL_RULES_PATH, get_account
from personal_mail_mcp.google import list_gmail_inbox_messages, list_gmail_unread_non_inbox_messages
from personal_mail_mcp.microsoft import list_inbox_messages, list_unread_non_inbox_messages


Message = dict[str, str | bool | None]


def audit_mail(account_ids: list[str], limit_per_account: int = 250) -> dict:
    messages = []
    for account_id in account_ids:
        account = get_account(account_id)
        if account.provider == "microsoft":
            account_messages = list_inbox_messages(account, limit=limit_per_account)
        elif account.provider == "google":
            account_messages = list_gmail_inbox_messages(account, limit=limit_per_account)
        else:
            raise ValueError(f"Unsupported provider for audit: {account.provider}")
        for message in account_messages:
            messages.append(_normalize_message(account_id, account.provider, message))

    messages.sort(key=lambda item: item.get("sort_date") or "", reverse=True)
    classified = classify_messages(messages)
    return {
        "accounts": account_ids,
        "total": len(messages),
        "counts": {action: len(items) for action, items in classified.items()},
        "buckets": classified,
    }


def archive_plan(account_ids: list[str], limit_per_account: int = 250) -> dict:
    audit = audit_mail(account_ids, limit_per_account=limit_per_account)
    return archive_plan_from_audit(audit)


def unread_non_inbox_scan(account_ids: list[str], limit_per_account: int = 100) -> dict:
    buckets = []
    for account_id in account_ids:
        account = get_account(account_id)
        if account.provider == "microsoft":
            messages = list_unread_non_inbox_messages(account, limit=limit_per_account)
        elif account.provider == "google":
            messages = list_gmail_unread_non_inbox_messages(account, limit=limit_per_account)
        else:
            raise ValueError(f"Unsupported provider for missed scan: {account.provider}")
        normalized = [_normalize_message(account_id, account.provider, message) for message in messages]
        classified = classify_messages(normalized)
        attention = classified["flag"] + classified["review"] + classified["keep"]
        buckets.append(
            {
                "account_id": account_id,
                "provider": account.provider,
                "count": len(messages),
                "attention_count": len(attention),
                "archive_or_noise_count": len(classified["archive"]),
                "attention": [_missed_message_summary(message, messages) for message in attention],
            }
        )
    return {
        "accounts": account_ids,
        "total": sum(bucket["count"] for bucket in buckets),
        "attention_total": sum(bucket["attention_count"] for bucket in buckets),
        "buckets": buckets,
    }


def archive_plan_from_audit(audit: dict) -> dict:
    grouped: dict[tuple[str, str, str], list[dict]] = {}
    for message in audit.get("buckets", {}).get("archive", []):
        key = (
            str(message.get("reason") or "archive"),
            _sender_key(str(message.get("from") or "")),
            _subject_key(str(message.get("subject") or "")),
        )
        grouped.setdefault(key, []).append(_plan_message(message))

    groups = [
        {
            "grouping": reason,
            "sender_key": sender_key,
            "subject_key": subject_key,
            "account_ids": sorted({str(message.get("account_id") or "") for message in messages}),
            "count": len(messages),
            "messages": messages,
        }
        for (reason, sender_key, subject_key), messages in grouped.items()
    ]
    return {
        "accounts": audit.get("accounts", []),
        "total": audit.get("total", 0),
        "archive_count": sum(group["count"] for group in groups),
        "groups": groups,
        "filter_recommendations": _filter_recommendations(groups),
    }


def classify_messages(messages: list[dict], rules: dict | None = None) -> dict[str, list[dict]]:
    if rules is None:
        rules = load_mail_rules()
    sample_keep_ids = _recent_sample_ids(messages, rules)
    buckets: dict[str, list[dict]] = {"keep": [], "flag": [], "archive": [], "review": []}

    for message in messages:
        subject = str(message.get("subject") or "")
        sender = str(message.get("from") or "")
        subject_l = subject.lower()
        sender_l = sender.lower()
        haystack = f"{subject_l} {sender_l}"
        age_days = _age_days(str(message.get("sort_date") or ""))

        action = "review"
        reason = "unknown/ambiguous"

        if _matches_rule_list(rules["explicit_keep"], subject_l, sender_l, haystack, age_days):
            action = "keep"
            reason = "explicit keep rule"
        elif message["id"] in sample_keep_ids:
            action = "keep"
            reason = "recent sample rule"
        elif _matches_rule_list(rules["explicit_archive"], subject_l, sender_l, haystack, age_days):
            action = "archive"
            reason = "explicit archive rule"
        elif _matches_rule_list(rules["age_archive"], subject_l, sender_l, haystack, age_days):
            action = "archive"
            reason = "age archive rule"
        elif _contains(haystack, rules["keep_terms"]):
            action = "keep"
            reason = "obligation/record/security/commitment"
        elif ("britbox" in sender_l or "peacock" in sender_l) and _contains(
            subject_l, rules["streaming_keep_terms"]
        ):
            action = "keep"
            reason = "streaming account/payment or football/world cup"
        elif "britbox" in sender_l or "peacock" in sender_l:
            action = "archive"
            reason = "streaming content promo"
        elif "zillow" in sender_l or "zillow" in subject_l or "kukun" in sender_l:
            action = "archive"
            reason = "real estate update"
        elif "[spam]" in subject_l:
            action = "archive"
            reason = "spam marker"
        elif _contains(haystack, rules["archive_terms"]):
            action = "archive"
            reason = "low-obligation marketing/content"
        elif _matches_sample_group(subject_l, sender_l, rules):
            action = "archive"
            reason = "older than recent sample"

        buckets[action].append({**message, "action": action, "reason": reason})

    return buckets


def _plan_message(message: dict) -> dict:
    return {
        "account_id": message.get("account_id"),
        "id": message.get("id"),
        "subject": message.get("subject"),
        "from": message.get("from"),
        "received": message.get("received"),
    }


def _missed_message_summary(message: dict, original_messages: list[dict]) -> dict:
    original = next((item for item in original_messages if item.get("id") == message.get("id")), {})
    return {
        "account_id": message.get("account_id"),
        "id": message.get("id"),
        "subject": message.get("subject"),
        "from": message.get("from"),
        "received": message.get("received"),
        "folder": original.get("folder") or original.get("labelIds"),
        "action": message.get("action"),
        "reason": message.get("reason"),
        "preview": message.get("preview"),
    }


def _filter_recommendations(groups: list[dict]) -> list[dict]:
    recommendations = []
    for group in groups:
        if group["count"] < 2 and len(group["account_ids"]) < 2:
            continue
        recommendations.append(
            {
                "sender_key": group["sender_key"],
                "subject_key": group["subject_key"],
                "account_ids": group["account_ids"],
                "message_count": group["count"],
                "suggested_action": "create mailbox/provider rule to archive or move future matching messages before inbox triage",
            }
        )
    return recommendations


def _sender_key(sender: str) -> str:
    match = re.search(r"<([^>]+)>", sender)
    value = match.group(1) if match else sender
    return value.strip().lower()


def _subject_key(subject: str) -> str:
    value = subject.lower()
    value = re.sub(r"\b(re|fw|fwd):\s*", "", value)
    value = re.sub(r"\b\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?\b", "{date}", value)
    value = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "{date}", value)
    value = re.sub(r"\b\d+\b", "{num}", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


BASE_KEEP_TERMS = [
    "tax",
    "bill",
    "billing",
    "payment",
    "invoice",
    "statement",
    "balance",
    "retirement",
    "insurance",
    "health",
    "medical",
    "dental",
    "security alert",
    "login",
    "access code",
    "password",
    "order confirmation",
    "shipped",
    "shipment",
    "delivered",
    "refund",
    "reservation",
    "ticket",
    "tickets",
    "appointment",
    "reminder",
    "confirmation",
    "scheduled",
    "upcoming",
    "secure email",
    "action required",
    "please review",
    "please contact",
]

BASE_ARCHIVE_TERMS = [
    "promo",
    "discount",
    "sale",
    "newsletter",
    "bonus offer",
    "cash back",
    "reward",
    "new arrivals",
    "vacations",
    "flights",
    "wishlist",
    "stream",
    "now streaming",
    "what to watch",
    "feedback",
    "survey",
    "pre-qualify",
    "home report",
    "new home listing",
    "zestimate",
    "happy hour",
    "free gift",
    "launch discount",
]

BASE_STREAMING_KEEP_TERMS = ["payment", "account", "billing", "subscription"]


def load_mail_rules(
    default_path: Path = DEFAULT_MAIL_RULES_PATH, local_path: Path = LOCAL_MAIL_RULES_PATH
) -> dict:
    rules = {
        "keep_terms": list(BASE_KEEP_TERMS),
        "archive_terms": list(BASE_ARCHIVE_TERMS),
        "streaming_keep_terms": list(BASE_STREAMING_KEEP_TERMS),
        "sample_groups": [],
        "explicit_keep": [],
        "explicit_archive": [],
        "age_archive": [],
    }
    for path in (default_path, local_path):
        if path.exists():
            _merge_rule_data(rules, tomllib.loads(path.read_text(encoding="utf-8")))
    for key in ("keep_terms", "archive_terms", "streaming_keep_terms"):
        rules[key] = _dedupe(rules[key])
    return rules


def _merge_rule_data(rules: dict, data: dict) -> None:
    terms = data.get("terms", {})
    rules["keep_terms"].extend(_lower_list(terms.get("keep", [])))
    rules["archive_terms"].extend(_lower_list(terms.get("archive", [])))
    rules["streaming_keep_terms"].extend(_lower_list(terms.get("streaming_keep", [])))
    for key in ("sample_groups", "explicit_keep", "explicit_archive", "age_archive"):
        rules[key].extend(_normalize_rule_items(data.get(key, [])))


def _normalize_rule_items(items: list[dict]) -> list[dict]:
    normalized = []
    for item in items:
        normalized.append(
            {
                **item,
                "sender_any": _lower_list(item.get("sender_any", [])),
                "sender_none": _lower_list(item.get("sender_none", [])),
                "subject_any": _lower_list(item.get("subject_any", [])),
                "subject_none": _lower_list(item.get("subject_none", [])),
                "haystack_any": _lower_list(item.get("haystack_any", [])),
                "haystack_none": _lower_list(item.get("haystack_none", [])),
                "unless_subject_any": _lower_list(item.get("unless_subject_any", [])),
            }
        )
    return normalized


def _lower_list(values: list[str]) -> list[str]:
    return [str(value).lower() for value in values]


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _recent_sample_ids(messages: list[dict], rules: dict) -> set[str]:
    seen = {str(group.get("name") or index): 0 for index, group in enumerate(rules["sample_groups"])}
    keep_ids = set()
    for message in messages:
        subject = str(message.get("subject") or "").lower()
        sender = str(message.get("from") or "").lower()
        haystack = f"{subject} {sender}"
        for index, group in enumerate(rules["sample_groups"]):
            key = str(group.get("name") or index)
            if _matches_rule(group, subject, sender, haystack, None):
                seen[key] += 1
                limit = int(group.get("keep_latest", 0))
                if seen[key] <= limit:
                    keep_ids.add(str(message["id"]))
                break
    return keep_ids


def _matches_sample_group(subject: str, sender: str, rules: dict) -> bool:
    haystack = f"{subject} {sender}"
    return any(_matches_rule(group, subject, sender, haystack, None) for group in rules["sample_groups"])


def _contains(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def _matches_rule_list(
    rule_list: list[dict], subject: str, sender: str, haystack: str, age_days: int | None
) -> bool:
    return any(_matches_rule(rule, subject, sender, haystack, age_days) for rule in rule_list)


def _matches_rule(
    rule: dict, subject: str, sender: str, haystack: str, age_days: int | None
) -> bool:
    older_than_days = rule.get("older_than_days")
    if older_than_days is not None:
        if age_days is None or age_days <= int(older_than_days):
            return False
    if _contains(subject, rule.get("unless_subject_any", [])):
        return False
    if rule.get("sender_any") and not _contains(sender, rule["sender_any"]):
        return False
    if rule.get("sender_none") and _contains(sender, rule["sender_none"]):
        return False
    if rule.get("subject_any") and not _contains(subject, rule["subject_any"]):
        return False
    if rule.get("subject_none") and _contains(subject, rule["subject_none"]):
        return False
    if rule.get("haystack_any") and not _contains(haystack, rule["haystack_any"]):
        return False
    if rule.get("haystack_none") and _contains(haystack, rule["haystack_none"]):
        return False
    return True


def _normalize_message(account_id: str, provider: str, message: Message) -> dict:
    if provider == "google":
        sender = str(message.get("from") or "")
        received = str(message.get("date") or "")
    else:
        sender = f"{message.get('from_name') or ''} <{message.get('from_address') or ''}>"
        received = str(message.get("received") or "")
    return {
        "account_id": account_id,
        "provider": provider,
        "id": message.get("id"),
        "subject": message.get("subject"),
        "from": sender,
        "received": received,
        "sort_date": _sort_date(received),
        "preview": message.get("preview") or message.get("snippet"),
    }


def _sort_date(value: str) -> str:
    if not value:
        return ""
    if "T" in value:
        return value
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return value
    return parsed.isoformat()


def _age_days(value: str) -> int | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return (now - parsed.astimezone(timezone.utc)).days
