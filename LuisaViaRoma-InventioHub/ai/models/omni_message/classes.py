from enum import Enum
from typing import Union, Literal, List
from pydantic.types import constr

from pydantic import BaseModel, Field, RootModel

from models.classes import BaseInput


class OmniMessageTaskType(str, Enum):
    APP = "APP"
    PUSH = "PUSH"


class OmniMessage(BaseInput):
    type: OmniMessageTaskType = Field(..., description="Omnichannel message task type")


class LLMOmniMessageAPPOut(BaseModel):
    type: Literal[OmniMessageTaskType.APP] = OmniMessageTaskType.APP
    title: str = Field(..., max_length=20, json_schema_extra={"trans_editable": True},
                       description="Compelling in-app message headline that captures attention and conveys premium value instantly")
    text: str = Field(..., max_length=100, json_schema_extra={"trans_editable": True},
                      description="Persuasive message body that expands on title with luxury positioning and clear benefit communication")
    CTAs: List[constr(max_length=20)] = Field(..., min_length=1, json_schema_extra={"trans_editable": True},
                     description="Elegant CTAs in sentence case that drives immediate engagement with sophisticated tone")

class LLMOmniMessagePUSHOut(BaseModel):
    type: Literal[OmniMessageTaskType.PUSH] = OmniMessageTaskType.PUSH
    title: str = Field(..., max_length=20, json_schema_extra={"trans_editable": True},
                       description="Attention-grabbing push notification title that cuts through noise with exclusive appeal")
    text: str = Field(..., max_length=100, json_schema_extra={"trans_editable": True},
                      description="Compelling push message that creates urgency and desire while maintaining brand sophistication")
    CTAs: List[constr(max_length=30)] = Field(..., min_length=1, json_schema_extra={"trans_editable": True},
                     description="Direct action-oriented CTAs that emphasizes immediate value and seamless app re-engagement")


# --- Merged classes ---------------------------------------------------------


class MergedAPP(OmniMessage, LLMOmniMessageAPPOut):
    pass


class MergedPUSH(OmniMessage, LLMOmniMessagePUSHOut):
    pass


class OmniMessageOut(RootModel[Union[MergedAPP, MergedPUSH]]):
    pass
