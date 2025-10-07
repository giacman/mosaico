from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class ContentType(str, Enum):
    HOMEPAGE = 'HOMEPAGE'
    EDITORIAL = 'EDITORIAL'
    OMNI_MESSAGE = 'OMNI_MESSAGE'
    OMNI_BANNER = 'OMNI_BANNER'
    NEWSLETTER = 'NEWSLETTER'
    MARKETING_CAMPAIGN = 'MARKETING_CAMPAIGN'
    SOCIAL_ORGANIC = 'SOCIAL_ORGANIC'
    SOCIAL_PAID = 'SOCIAL_PAID'


class Gender(str, Enum):
    MEN = 'MEN'
    WOMEN = 'WOMEN'
    KIDS = 'KIDS'
    HOME = "HOME"
    BEAUTY = "BEAUTY"
    ALL = "ALL"


class BaseInput(BaseModel):
    theme: str = Field(..., description="General theme of the material to be generated")
    gender: Gender = Field(..., description="Gender that the material to be generated is aimed at")
    season: str = Field(..., description="")
    brands: List[str] = Field([], description="List of brands to promote")
    targets: List[str] = Field([],
                               description="List of reference targets that the material to be generated is aimed at")
    products: List[str] = Field([], description="List of descriptions of products to promote")
    product_category: str = Field("", description="Category of products to promote")
    additional_content: str = Field("", description="Additional information regarding the material to be generated")
