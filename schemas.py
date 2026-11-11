from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

PLAIN_LANGUAGE_MAX = 400


class Location(BaseModel):
    kind: Literal["page", "paragraph"]
    number: int = Field(ge=1)


class Quote(BaseModel):
    text: str = Field(min_length=1)
    location: Location


class Finding(BaseModel):
    item_id: str
    found: bool
    risk: Literal["Low", "Medium", "High"]
    explanation: str = Field(min_length=1)
    plain_language: str | None = None
    quotes: list[Quote] = Field(default_factory=list, max_length=3)

    @field_validator("plain_language")
    @classmethod
    def shorten_plain_language(cls, value: str | None) -> str | None:
        if value and len(value) > PLAIN_LANGUAGE_MAX:
            return value[: PLAIN_LANGUAGE_MAX - 1] + "…"
        return value


class CheckResult(BaseModel):
    results: list[Finding]

SINGLE_LINE = r"^[^\r\n]*$"


class SummaryItem(BaseModel):
    label: str = Field(min_length=1, max_length=100, pattern=SINGLE_LINE)
    status: Literal["quote_verified", "unverified", "possibly_present", "not_found"]
    risk: Literal["Low", "Medium", "High"]


class ContactRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100, pattern=SINGLE_LINE)
    email: EmailStr
    description: str = Field(min_length=1, max_length=1000)
    contract_type: Literal["employment", "lease", "business"]
    consent: Literal[True]
    summary: list[SummaryItem] = Field(default_factory=list, max_length=30)
    website: str = ""  # honeypot: humans never see or fill this field