from enum import Enum
from typing import List

from pydantic import BaseModel, Field
from pydantic.types import constr
from models.classes import BaseInput


class SocialPaidType(str, Enum):
    BRAND_AWARENESS = "BRAND_AWARENESS"
    CONVERSIONS = "CONVERSIONS"
    CATALOGUE_SALES = "CATALOGUE_SALES"
    VIDEO_VIEWS = "VIDEO_VIEWS"
    PRODUCT_CATALOG = "PRODUCT_CATALOG"


class SocialPaid(BaseInput):
    type: SocialPaidType = Field(..., description="The campaign objective type for paid social advertising")
    name: str = Field("", description="Campaign name for internal tracking and organization")


class LLMSocialPaidOut(BaseModel):
    title: str = Field(..., json_schema_extra={"trans_editable": True},
                       description="Eye-catching headline that stops scrolling, communicates value proposition instantly, and aligns with campaign objective",
                       max_length=40)
    text: str = Field(..., json_schema_extra={"trans_editable": True},
                      description="Persuasive body copy that expands on title promise, addresses pain points/desires, and guides toward CTA action",
                      max_length=100)
    CTAs: List[constr(max_length=30)] = Field(..., min_lenght=1, json_schema_extra={"trans_editable": True},
                     description="Action-oriented CTAs using strong verbs, creating urgency without being pushy, platform-optimized")


class SocialPaidOut(SocialPaid, LLMSocialPaidOut):
    pass
