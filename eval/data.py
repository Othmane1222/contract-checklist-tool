from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ManifestEntry(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9-]+$")
    file: str
    contract_type: Literal["employment", "lease", "business"]
    split: Literal["dev", "heldout"]
    source: str = Field(min_length=1)


class Manifest(BaseModel):
    contracts: list[ManifestEntry]


class ItemLabel(BaseModel):
    found: bool
    risk: Literal["Low", "Medium", "High"] | None = None
    articles: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def risk_when_found(self):
        if self.found and self.risk is None:
            raise ValueError("risk is required when found is true")
        return self


class GroundTruth(BaseModel):
    contract_id: str
    items: dict[str, ItemLabel]