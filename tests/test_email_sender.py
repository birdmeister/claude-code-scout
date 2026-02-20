"""Tests for src/email_sender.py — mocked Resend API calls."""

from unittest.mock import patch, MagicMock

from src.email_sender import send_report


@patch("src.email_sender.resend")
def test_send_report_success(mock_resend):
    result = send_report(
        api_key="test-key",
        from_address="scout@test.com",
        to_address="user@test.com",
        subject_prefix="[Test]",
        report_markdown="# Report",
    )
    assert result is True
    assert mock_resend.api_key == "test-key"
    mock_resend.Emails.send.assert_called_once()

    call_args = mock_resend.Emails.send.call_args[0][0]
    assert call_args["from"] == "scout@test.com"
    assert call_args["to"] == ["user@test.com"]
    assert call_args["text"] == "# Report"


@patch("src.email_sender.resend")
def test_send_report_failure(mock_resend):
    mock_resend.Emails.send.side_effect = RuntimeError("Send failed")
    result = send_report(
        api_key="key",
        from_address="a@b.com",
        to_address="c@d.com",
        subject_prefix="[X]",
        report_markdown="text",
    )
    assert result is False
