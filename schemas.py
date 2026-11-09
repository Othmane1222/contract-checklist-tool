from typing import Literal

from pydantic import BaseModel, Field


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
    quotes: list[Quote] = Field(default_factory=list, max_length=3)


class CheckResult(BaseModel):
    results: list[Finding]