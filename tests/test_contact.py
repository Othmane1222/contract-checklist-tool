import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

import main
from mailer import build_message
from ratelimit import RateLimiter
from schemas import ContactRequest

VALID = {
    "name": "Daniel Torres",
    "email": "daniel@example.com",
    "description": "Please review my probation clause.",
    "contract_type": "employment",
    "consent": True,
}


def make_request(**changes):
    return ContactRequest(**{**VALID, **changes})


def test_valid_request_is_accepted():
    assert make_request().name == "Daniel Torres"


@pytest.mark.parametrize("changes", [
    {"name": "Daniel\r\nBcc: victim@example.com"},
    {"email": "daniel@example.com\nBcc: victim@example.com"},
    {"email": "not-an-email"},
    {"consent": False},
    {"description": "x" * 1001},
    {"contract_type": "other"},
])
def test_invalid_requests_are_rejected(changes):
    with pytest.raises(ValidationError):
        make_request(**changes)


def test_summary_never_contains_quote_text():
    request = make_request(summary=[{
        "label": "Probation period",
        "status": "quote_verified",
        "risk": "High",
        "quotes": [{"text": "其中试用期为六个月"}],
    }])
    body = build_message(request, "sender@qq.com", "lawyer@example.com").get_content()
    assert "Probation period" in body
    assert "试用期" not in body


def test_reply_to_is_the_users_email():
    message = build_message(make_request(), "sender@qq.com", "lawyer@example.com")
    assert message["Reply-To"] == "daniel@example.com"
    assert message["From"] == "sender@qq.com"


def test_rate_limit_blocks_fourth_message():
    limiter = RateLimiter(max_requests=3, window_seconds=600)
    assert all(limiter.allow("1.2.3.4", now=t) for t in (0, 1, 2))
    assert not limiter.allow("1.2.3.4", now=3)
    assert limiter.allow("1.2.3.4", now=601)


def test_honeypot_pretends_success_without_sending(monkeypatch):
    def fail(_):
        raise AssertionError("email must not be sent")

    monkeypatch.setattr(main, "send_contact_email", fail)
    client = TestClient(main.app)
    response = client.post("/api/contact", json={**VALID, "website": "http://spam.example"})
    assert response.status_code == 200