from app.security.redaction import redact_mapping


def test_redaction_removes_nested_tokens() -> None:
    safe = redact_mapping(
        {"Authorization": "Bearer abc", "buyer": {"email": "a@b.test"}, "status": "ok"}
    )
    assert safe == {
        "Authorization": "[REDACTED]",
        "buyer": {"email": "[REDACTED]"},
        "status": "ok",
    }


def test_redaction_handles_lists_of_mappings() -> None:
    safe = redact_mapping({"events": [{"token": "abc"}, {"status": "ok"}]})
    assert safe == {"events": [{"token": "[REDACTED]"}, {"status": "ok"}]}


def test_redaction_is_case_insensitive_on_keys() -> None:
    safe = redact_mapping({"AUTHORIZATION": "Bearer abc"})
    assert safe == {"AUTHORIZATION": "[REDACTED]"}
