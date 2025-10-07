from enum import Enum
from typing import Union, Literal

from pydantic import BaseModel, Field, RootModel

from models.classes import BaseInput


class Social(str, Enum):
    INSTAGRAM = "INSTAGRAM"
    TIKTOK = "TIKTOK"
    LINKEDIN = "LINKEDIN"


class SocialOrganic(BaseInput):
    type: Social = Field(..., description="The social network platform for content generation")


class LLMSocialOrganicINSTAGRAMOut(BaseModel):
    type: Literal[Social.INSTAGRAM] = Social.INSTAGRAM
    text: str = Field(
        ...,
        max_length=200,
        json_schema_extra={"trans_editable": True},
        description="Instagram post copy that engages visually-oriented audience with hashtags, emojis when appropriate, and clear CTA"
    )


class LLMSocialOrganicTIKTOKOut(BaseModel):
    type: Literal[Social.TIKTOK] = Social.TIKTOK
    text: str = Field(
        ...,
        max_length=200,
        json_schema_extra={"trans_editable": True},
        description="TikTok video caption that hooks attention immediately, uses trending hashtags, and encourages interaction"
    )


class LLMSocialOrganicLINKEDINOut(BaseModel):
    type: Literal[Social.LINKEDIN] = Social.LINKEDIN
    text: str = Field(
        ...,
        json_schema_extra={"trans_editable": True},
        description="LinkedIn post text that positions brand professionally, shares insights, and stimulates business discussions"
    )


# --- Merged classes -------------------------------------------------------

class MergedINSTAGRAM(SocialOrganic, LLMSocialOrganicINSTAGRAMOut):
    pass


class MergedTIKTOK(SocialOrganic, LLMSocialOrganicTIKTOKOut):
    pass


class MergedLINKEDIN(SocialOrganic, LLMSocialOrganicLINKEDINOut):
    pass


class SocialOrganicOut(
    RootModel[Union[MergedINSTAGRAM, MergedTIKTOK, MergedLINKEDIN]]
):
    pass
