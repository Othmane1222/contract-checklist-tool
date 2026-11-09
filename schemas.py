from typing import Literal

from pydantic import BaseModel, Field, field_validator

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