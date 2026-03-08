from pydantic import BaseModel
from typing import List


class Section(BaseModel):
    title: str
    subsections: List[str]


class BlogPlan(BaseModel):
    title: str
    sections: List[Section]