from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from checklists import load_checklist
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
    item_id: str = Field(min_length=1, max_length=50, pattern=r"^[a-z_]+$")
    status: Literal["quote_verified", "unverified", "possibly_present", "not_found"]
    risk: Literal["Low", "Medium", "High"]


class ContactRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100, pattern=SINGLE_LINE)
    email: EmailStr
    description: str = Field(min_length=1, max_length=1000)
    contract_type: Literal["employment", "lease", "business"]
    consent: Literal[True]
    summary: list[SummaryItem] = Field(default_factory=list, max_length=30)
    user_language: Literal["en", "es", "zh"] = "en"
    website: str = ""  # honeypot: humans never see or fill this field
    
    @model_validator(mode="after")
    def check_summary_items(self):
        known = {item["id"] for item in load_checklist(self.contract_type)["items"]}
        if any(entry.item_id not in known for entry in self.summary):
            raise ValueError("Unknown checklist item in summary.")
        return self