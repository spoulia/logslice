"""Tests for logslice.redact."""

import pytest
from logslice.redact import (
    DEFAULT_PATTERNS,
    PLACEHOLDER,
    redact_entry,
    redact_fields,
    redact_string,
)


# ---------------------------------------------------------------------------
# redact_string
# ---------------------------------------------------------------------------

class TestRedactString:
    def test_email_is_masked(self):
        result = redact_string("contact user@example.com now")
        assert "user@example.com" not in result
        assert PLACEHOLDER in result

    def test_ipv4_is_masked(self):
        result = redact_string("request from 192.168.1.42 failed")
        assert "192.168.1.42" not in result
        assert PLACEHOLDER in result

    def test_hex_token_is_masked(self):
        token = "a" * 32
        result = redact_string(f"token={token}")
        assert token not in result
        assert PLACEHOLDER in result

    def test_no_sensitive_data_unchanged(self):
        text = "ordinary log message without secrets"
        assert redact_string(text) == text

    def test_custom_placeholder(self):
        result = redact_string("mail me@x.io", placeholder="***")
        assert "***" in result

    def test_custom_patterns_override_defaults(self):
        # With a custom pattern that matches 'SECRET', defaults don't fire
        result = redact_string("value=SECRET", patterns=[r"SECRET"])
        assert "SECRET" not in result
        # An email present should NOT be redacted because defaults are overridden
        result2 = redact_string("a@b.com", patterns=[r"SECRET"])
        assert "a@b.com" in result2


# ---------------------------------------------------------------------------
# redact_fields
# ---------------------------------------------------------------------------

class TestRedactFields:
    def test_named_field_replaced(self):
        entry = {"message": "hello", "user": "alice", "level": "INFO"}
        result = redact_fields(entry, ["user"])
        assert result["user"] == PLACEHOLDER
        assert result["message"] == "hello"

    def test_missing_field_ignored(self):
        entry = {"message": "hi"}
        result = redact_fields(entry, ["password"])
        assert "password" not in result

    def test_original_entry_not_mutated(self):
        entry = {"user": "bob"}
        redact_fields(entry, ["user"])
        assert entry["user"] == "bob"


# ---------------------------------------------------------------------------
# redact_entry
# ---------------------------------------------------------------------------

class TestRedactEntry:
    def test_message_patterns_applied(self):
        entry = {"message": "login from 10.0.0.1", "level": "INFO"}
        result = redact_entry(entry)
        assert "10.0.0.1" not in result["message"]

    def test_field_and_pattern_combined(self):
        entry = {"message": "ok", "token": "abc", "ip": "1.2.3.4"}
        result = redact_entry(entry, fields=["token"])
        assert result["token"] == PLACEHOLDER
        assert "1.2.3.4" not in result["ip"]

    def test_empty_entry_unchanged(self):
        assert redact_entry({}) == {}

    def test_non_string_fields_untouched(self):
        entry = {"count": 42, "active": True}
        result = redact_entry(entry)
        assert result["count"] == 42
        assert result["active"] is True
