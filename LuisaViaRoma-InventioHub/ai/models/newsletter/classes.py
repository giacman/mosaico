from enum import Enum
from typing import List

from pydantic import BaseModel, Field
from models.classes import BaseInput


class NewsletterType(str, Enum):
    EDITORIAL = "EDITORIAL"
    PROMO = "PROMO"
    CATEGORY = "CATEGORY"


class Newsletter(BaseInput):
    type: NewsletterType = Field(..., description="The type of newsletter")
    number_of_elements: int = Field(..., description="The number of newsletter elements to generate")


class NewsletterElementOut(BaseModel):
    title: str = Field(..., max_length=30, json_schema_extra={"trans_editable": True},
                       description="Section title, clear and scannable, category-specific, max 3 words")
    text: str = Field(..., min_length=50, max_length=200, json_schema_extra={"trans_editable": True},
                      description="Block description that balances information and persuasion with relevant details without overwhelming")
    CTAs: List[str] = Field(..., json_schema_extra={"trans_editable": True},
                     description="Specific call-to-action in sentence case with clear action verb, max 3 words")


class LLMNewsletterOut(BaseModel):
    subject_line: str = Field(..., max_length=70, json_schema_extra={"trans_editable": True},
                              description="Email subject that captures attention and stimulates opening, avoiding spam triggers and personalizing when possible")
    preheader: str = Field("", max_length=50, json_schema_extra={"trans_editable": True},
                           description="Preview text that complements subject with additional context, amplifying message with added value or soft call-to-action")
    elements: List[NewsletterElementOut] = Field(..., description="The list of newsletter elements")


class NewsletterOut(Newsletter, LLMNewsletterOut):
    pass
