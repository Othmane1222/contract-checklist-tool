ERROR_MESSAGES = {
    "invalid_request": "Something in the request was missing or invalid.",
    "length_required": "The upload was incomplete. Please try again.",
    "invalid_contract_type": "Please choose a contract type.",
    "invalid_language": "Please choose a language.",
    "unsupported_file_type": "Only PDF and DOCX files are supported.",
    "file_empty": "The file is empty.",
    "file_too_large": "The file is too large. The limit is {max_mb} MB.",
    "file_unreadable": "Could not read this file. It may be damaged or password-protected.",
    "no_text_found": "No text found. Scanned PDFs are not supported yet.",
    "ai_rate_limited": "Too many requests. Please wait a minute and try again.",
    "ai_timeout": "The AI service took too long. Please try again.",
    "ai_unreachable": "Could not reach the AI service. Please check the internet connection and try again.",
    "ai_failed": "The AI service failed. Please try again.",
    "contact_invalid": "Please check your name, email and message, and tick the consent box.",
    "contact_rate_limited": "Too many messages. Please try again later.",
    "contact_send_failed": "We couldn't send your message. Please email {email} directly.",
    "contact_send_failed_no_fallback": "We couldn't send your message. Please try again later.",
}


class AppError(Exception):
    """An error the page can show to the user, identified by a code."""

    def __init__(self, status_code: int, code: str, **params):
        if code not in ERROR_MESSAGES:
            raise ValueError(f"Unknown error code: {code}")
        super().__init__(code)
        self.status_code = status_code
        self.code = code
        self.params = params


def error_body(code: str, **params) -> dict:
    return {"code": code, "message": ERROR_MESSAGES[code].format(**params), "params": params}