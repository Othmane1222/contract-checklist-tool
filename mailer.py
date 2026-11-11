import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

from schemas import ContactRequest

load_dotenv()

SMTP_TIMEOUT_SECONDS = 10
STATUS_TEXT = {
    "quote_verified": "source found",
    "unverified": "unverified",
    "possibly_present": "possibly present",
    "not_found": "not found",
}


def build_message(request: ContactRequest, sender: str, recipient: str) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = f"Contract checklist: help request ({request.contract_type})"
    message["From"] = sender
    message["To"] = recipient
    message["Reply-To"] = str(request.email)

    lines = [
        f"Name: {request.name}",
        f"Email: {request.email}",
        f"Contract type: {request.contract_type}",
        "",
        "Message:",
        request.description,
    ]
    if request.summary:
        lines += ["", "Checklist summary (no contract text):"]
        lines += [f"- {item.label}: {STATUS_TEXT[item.status]}, {item.risk} risk" for item in request.summary]
    message.set_content("\n".join(lines))
    return message


def send_contact_email(request: ContactRequest) -> None:
    host = os.environ["SMTP_HOST"]
    port = int(os.getenv("SMTP_PORT", "465"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    message = build_message(request, sender=user, recipient=os.environ["CONTACT_RECIPIENT"])

    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=SMTP_TIMEOUT_SECONDS) as server:
            server.login(user, password)
            server.send_message(message)
    else:
        with smtplib.SMTP(host, port, timeout=SMTP_TIMEOUT_SECONDS) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(message)