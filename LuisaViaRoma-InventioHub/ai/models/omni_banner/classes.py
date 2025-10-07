from enum import Enum
from typing import Union, Literal, List

from pydantic import BaseModel, Field, RootModel
from pydantic.types import constr
from models.classes import BaseInput


class OmniBannerTaskType(str, Enum):
    SCENES = "SCENES"
    DYBANNERS_APP = "DYBANNERS_APP"
    DYBANNERS_SITE_CATALOG = "DYBANNERS_SITE_CATALOG"
    DYBANNERS_SITE_LEVEL = "DYBANNERS_SITE_LEVEL"
    DYCAMPAIGNS_PROD_PAGE = "DYCAMPAIGNS_PROD_PAGE"
    LVR_STORIES = "LVR_STORIES"
    RIBBON = "RIBBON"
    POP_UP = "POP_UP"


class OmniBanner(BaseInput):
    type: OmniBannerTaskType = Field(..., description="Omnichannel banner task type")


class LLMOmniBannerSCENESOut(BaseModel):
    type: Literal[OmniBannerTaskType.SCENES] = OmniBannerTaskType.SCENES
    text: str = Field(..., max_length=30, json_schema_extra={"trans_editable": True},
                      description="Brief scene text that captures brand essence and accompanies visual content with emotional impact")
    CTAs: List[constr(max_length=30)] = Field(..., min_length=1, json_schema_extra={"trans_editable": True},
                     description="Elegant CTAs in sentence case that invites user to continue the experience")


class LLMOmniBannerDYBANNERSAPPOut(BaseModel):
    type: Literal[OmniBannerTaskType.DYBANNERS_APP] = OmniBannerTaskType.DYBANNERS_APP
    title: str = Field(..., max_length=25, json_schema_extra={"trans_editable": True},
                       description="Exclusive headline that conveys VIP access and premium value proposition")
    text: str = Field(..., max_length=65, json_schema_extra={"trans_editable": True},
                      description="Dynamic message that reinforces luxury perception and stimulates immediate interaction")
    CTAs: List[str] = Field(..., max_length=30, json_schema_extra={"trans_editable": True},
                     description="Action-oriented CTA that emphasizes exclusivity and urgency")


class LLMOmniBannerDYBANNERSSITECATALOGOut(BaseModel):
    type: Literal[OmniBannerTaskType.DYBANNERS_SITE_CATALOG] = OmniBannerTaskType.DYBANNERS_SITE_CATALOG
    title: str = Field(..., json_schema_extra={"trans_editable": True},
                       description="Category-focused headline that highlights product collections and creates desirability")
    text: str = Field(..., json_schema_extra={"trans_editable": True},
                      description="Supporting text that emphasizes product categories and creates urgency while maintaining premium tone")
    CTAs: List[str] = Field(..., json_schema_extra={"trans_editable": True},
                     description="Discovery-oriented CTAs that guides users to explore catalog sections")


class LLMOmniBannerDYBANNERSSITELEVELOut(BaseModel):
    type: Literal[OmniBannerTaskType.DYBANNERS_SITE_LEVEL] = OmniBannerTaskType.DYBANNERS_SITE_LEVEL
    text: str = Field(..., max_length=80, json_schema_extra={"trans_editable": True},
                      description="Site-wide message differentiated for new vs returning users, focusing on personalized discovery")
    CTAs: List[constr(max_length=30)] = Field(..., min_length=1, json_schema_extra={"trans_editable": True},
                     description="Elegant action that strengthens brand connection and guides personalized exploration")


class LLMOmniBannerDYCAMPAIGNSPRODPAGEOut(BaseModel):
    type: Literal[OmniBannerTaskType.DYCAMPAIGNS_PROD_PAGE] = OmniBannerTaskType.DYCAMPAIGNS_PROD_PAGE
    text: str = Field(..., max_length=40, json_schema_extra={"trans_editable": True},
                      description="Hyper-targeted copy that highlights product uniqueness and guides toward purchase decision")


class LLMOmniBannerLVRSTORIESOut(BaseModel):
    type: Literal[OmniBannerTaskType.LVR_STORIES] = OmniBannerTaskType.LVR_STORIES
    text: str = Field(..., max_length=80, json_schema_extra={"trans_editable": True},
                      description="Narrative fragment with evocative language that creates emotional engagement alongside fashion visuals")
    CTAs: List[constr(max_length=30)] = Field(..., min_length=1, json_schema_extra={"trans_editable": True},
                     description="Soft invitation that encourages deeper exploration and discovery")


class LLMOmniBannerRIBBONOut(BaseModel):
    type: Literal[OmniBannerTaskType.RIBBON] = OmniBannerTaskType.RIBBON
    text: str = Field(..., max_length=65, json_schema_extra={"trans_editable": True},
                      description="Essential text for persistent ribbon communicating flash promotions or exclusive benefits")
    text_and_cta: str = Field(..., max_length=65, json_schema_extra={"trans_editable": True},
                              description="Combined text and action that maintains sophisticated tone while conveying special initiatives")


class LLMOmniBannerPOPUPOut(BaseModel):
    type: Literal[OmniBannerTaskType.POP_UP] = OmniBannerTaskType.POP_UP
    text: str = Field(..., max_length=80, json_schema_extra={"trans_editable": True},
                      description="Persuasive modal text for lead capture or limited-time offers that immediately captures attention")
    CTAs: List[constr(max_length=30)] = Field(..., min_length=1, json_schema_extra={"trans_editable": True},
                     description="Direct action-oriented CTA that reinforces perceived value and guides user to conversion")


# --- Merged classes ---------------------------------------------------------

class MergedSCENES(OmniBanner, LLMOmniBannerSCENESOut):
    pass


class MergedDYBANNERSAPP(OmniBanner, LLMOmniBannerDYBANNERSAPPOut):
    pass


class MergedDYBANNERSSITECATALOG(OmniBanner, LLMOmniBannerDYBANNERSSITECATALOGOut):
    pass


class MergedDYBANNERSSITELEVEL(OmniBanner, LLMOmniBannerDYBANNERSSITELEVELOut):
    pass


class MergedDYCAMPAIGNSPRODPAGE(OmniBanner, LLMOmniBannerDYCAMPAIGNSPRODPAGEOut):
    pass


class MergedLVRSTORIES(OmniBanner, LLMOmniBannerLVRSTORIESOut):
    pass


class MergedRIBBON(OmniBanner, LLMOmniBannerRIBBONOut):
    pass


class MergedPOPUP(OmniBanner, LLMOmniBannerPOPUPOut):
    pass


class OmniBannerOut(
    RootModel[
        Union[
            MergedSCENES,
            MergedDYBANNERSAPP,
            MergedDYBANNERSSITECATALOG,
            MergedDYBANNERSSITELEVEL,
            MergedDYCAMPAIGNSPRODPAGE,
            MergedLVRSTORIES,
            MergedRIBBON,
            MergedPOPUP,
        ]
    ]
):
    pass
