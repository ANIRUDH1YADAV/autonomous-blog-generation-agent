from typing import Literal

from pydantic import BaseModel, Field, field_validator


class RouterDecision(BaseModel):
    decision: Literal["search", "direct"]

    @field_validator("decision", mode="before")
    @classmethod
    def normalize_decision(cls, value):
        return str(value).strip().lower()


class EvidenceItem(BaseModel):
    title: str
    url: str = ""
    content: str


class LLMKnowledgeOutput(BaseModel):
    evidence: list[EvidenceItem] = Field(default_factory=list)


class BrainstormingOutput(BaseModel):
    title: str
    headings: list[str] = Field(default_factory=list)


class ContentDraftOutput(BaseModel):
    draft_blog: str


class TranslationOutput(BaseModel):
    draft_blog: str


class SEOOutput(BaseModel):
    final_blog: str
    meta_description: str = ""
    keywords: list[str] = Field(default_factory=list)
