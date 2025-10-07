from enum import Enum
from typing import Union, List

from pydantic import Field, BaseModel, RootModel

from models.classes import BaseInput


class CampaignType(str, Enum):
    AFFILIATION_LANDING = "AFFILIATION_LANDING"
    AFFILIATION_BANNER = "AFFILIATION_BANNER"
    PROGRAMMATIC_BANNER = "PROGRAMMATIC_BANNER"


class MarketingCampaign(BaseInput):
    type: CampaignType = Field(..., description="Type of campaign")
    only_title: bool = Field(False, description="If true, generate only title.")
    title_char_limit: int = Field(-1, description="The maximum number of characters allowed for the title.")
    text_char_limit: int = Field(-1, description="The maximum number of characters allowed for the text.")
    cta_char_limit: int = Field(-1, description="The maximum number of characters allowed for the cta.")


class LLMMarketingCampaignAFFILIATIONLANDINGOut(BaseModel):
    title: str = Field(..., json_schema_extra={"trans_editable": True},
                       description="Main campaign headline that captures attention and communicates core value using power words and tangible benefits")
    text: str = Field("", json_schema_extra={"trans_editable": True},
                      description="Campaign message body that develops value proposition with convincing details, includes social proof when possible, and focuses on concrete user advantages")


class LLMMarketingCampaignAFFILIATIONBANNEROut(BaseModel):
    title: str = Field(..., json_schema_extra={"trans_editable": True},
                       description="Main campaign headline that captures attention and communicates core value using power words and tangible benefits")
    text: str = Field(..., json_schema_extra={"trans_editable": True},
                      description="Campaign message body that develops value proposition with convincing details, includes social proof when possible, and focuses on concrete user advantages")
    CTAs: List[str] = Field(..., json_schema_extra={"trans_editable": True},
                     description="CTAs with specific urgent action verb in sentence case that clearly communicates expected action")


class LLMMarketingCampaignPROGRAMMATICBANNEROut(LLMMarketingCampaignAFFILIATIONBANNEROut):
    pass


# --- Merged classes ---------------------------------------------------------

class MergedAFFILIATIONLANDING(MarketingCampaign, LLMMarketingCampaignAFFILIATIONLANDINGOut):
    pass


class MergedAFFILIATIONBANNER(MarketingCampaign, LLMMarketingCampaignAFFILIATIONBANNEROut):
    pass


class MergedPROGRAMMATICBANNER(MarketingCampaign, LLMMarketingCampaignPROGRAMMATICBANNEROut):
    pass


class MarketingCampaignOut(
    RootModel[Union[MergedAFFILIATIONLANDING, MergedAFFILIATIONBANNER, MergedPROGRAMMATICBANNER]]):
    pass
