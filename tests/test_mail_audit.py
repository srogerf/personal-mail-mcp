from personal_mail_mcp.mail_audit import archive_plan_from_audit, classify_messages


def _rules() -> dict:
    return {
        "keep_terms": ["bill", "payment", "security", "secure email"],
        "archive_terms": ["newsletter", "survey"],
        "streaming_keep_terms": ["billing"],
        "sample_groups": [
            {"name": "guitar", "sender_any": ["guitar-pro"], "keep_latest": 1},
        ],
        "explicit_keep": [],
        "explicit_archive": [
            {"sender_any": ["example promo"]},
        ],
        "age_archive": [
            {
                "sender_any": ["brokerage"],
                "older_than_days": 7,
                "unless_subject_any": ["appointment", "secure email"],
            }
        ],
    }


def test_sample_group_keeps_latest_and_archives_older() -> None:
    messages = [
        {
            "id": "latest",
            "subject": "Latest lesson",
            "from": "Guitar-Pro <news@guitar-pro.com>",
            "sort_date": "2026-04-30T12:00:00Z",
        },
        {
            "id": "older",
            "subject": "Older lesson",
            "from": "Guitar-Pro <news@guitar-pro.com>",
            "sort_date": "2026-04-29T12:00:00Z",
        },
    ]

    buckets = classify_messages(messages, rules=_rules())

    assert [message["id"] for message in buckets["keep"]] == ["latest"]
    assert [message["id"] for message in buckets["archive"]] == ["older"]
    assert buckets["archive"][0]["reason"] == "older than recent sample"


def test_age_archive_takes_precedence_over_keep_terms() -> None:
    messages = [
        {
            "id": "old-info",
            "subject": "Your payment info is ready",
            "from": "Example Brokerage <updates@brokerage.example>",
            "sort_date": "2026-04-01T12:00:00Z",
        },
        {
            "id": "old-secure",
            "subject": "You have a secure email",
            "from": "Example Brokerage <updates@brokerage.example>",
            "sort_date": "2026-04-01T12:00:00Z",
        },
    ]

    buckets = classify_messages(messages, rules=_rules())

    assert [message["id"] for message in buckets["archive"]] == ["old-info"]
    assert buckets["archive"][0]["reason"] == "age archive rule"
    assert [message["id"] for message in buckets["keep"]] == ["old-secure"]


def test_archive_plan_groups_across_accounts_and_recommends_filters() -> None:
    audit = {
        "accounts": ["a", "b"],
        "total": 3,
        "buckets": {
            "archive": [
                {
                    "account_id": "a",
                    "id": "1",
                    "subject": "Fretboards Lab lesson 101",
                    "from": "Sender <s@example.com>",
                    "received": "2026-04-30T12:00:00Z",
                    "reason": "low-obligation marketing/content",
                },
                {
                    "account_id": "b",
                    "id": "2",
                    "subject": "Fretboards Lab lesson 102",
                    "from": "Sender <s@example.com>",
                    "received": "2026-04-30T13:00:00Z",
                    "reason": "low-obligation marketing/content",
                },
                {
                    "account_id": "b",
                    "id": "3",
                    "subject": "Old update",
                    "from": "Other <o@example.com>",
                    "received": "2026-04-01T12:00:00Z",
                    "reason": "age archive rule",
                },
            ]
        },
    }

    plan = archive_plan_from_audit(audit)

    assert plan["archive_count"] == 3
    assert plan["groups"][0]["grouping"] == "low-obligation marketing/content"
    assert plan["groups"][0]["account_ids"] == ["a", "b"]
    assert plan["groups"][0]["sender_key"] == "s@example.com"
    assert plan["groups"][0]["subject_key"] == "fretboards lab lesson {num}"
    assert plan["groups"][0]["messages"] == [
        {
            "account_id": "a",
            "id": "1",
            "subject": "Fretboards Lab lesson 101",
            "from": "Sender <s@example.com>",
            "received": "2026-04-30T12:00:00Z",
        },
        {
            "account_id": "b",
            "id": "2",
            "subject": "Fretboards Lab lesson 102",
            "from": "Sender <s@example.com>",
            "received": "2026-04-30T13:00:00Z",
        },
    ]
    assert plan["filter_recommendations"] == [
        {
            "sender_key": "s@example.com",
            "subject_key": "fretboards lab lesson {num}",
            "account_ids": ["a", "b"],
            "message_count": 2,
            "suggested_action": "create mailbox/provider rule to archive or move future matching messages before inbox triage",
        }
    ]
