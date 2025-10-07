from enum import Enum
from typing import List

from pydantic import BaseModel, Field, HttpUrl, model_validator
from typing_extensions import Self

from models.classes import Gender


class LabelType(str, Enum):
    TITLE = 'TITLE'
    TEXT = 'TEXT'
    WIDGET = 'WIDGET'
    CTA = 'CTA'
    COMPOSED = 'COMPOSED'


class Device(str, Enum):
    HP = 'HP'
    APP = 'APP'


class LLMHomepageElement(BaseModel):
    type: LabelType = Field(..., description="")
    theme: str = Field(..., description="Name of the theme or section")
    comment: str = Field("", description="Development notes or internal comments")


class HomepageElement(LLMHomepageElement):
    label: str = Field(..., description="Key for the text to display (e.g. LBL_...)")
    link: str = Field("", description="URL associated with the element") # HttpUrl |

class ComposedElement(HomepageElement):
    elements: List[HomepageElement] = Field(..., description="Sub-elements that compose this composite element")


class Homepage(BaseModel):
    gender: Gender = Field(..., description="Reference gender")
    device: Device = Field(..., description="Device")
    elements: List[HomepageElement | ComposedElement] = Field(...,
                                                              description="List of blocks that compose the homepage")


class HomepageElementOut(HomepageElement):
    text: str = Field(..., json_schema_extra={"trans_editable": True},
                      description="Text associated with the label. If type == TITLE -> len(text)<=30. If type == TEXT -> len(text)<=50.")

    @model_validator(mode="after")
    def check_text_by_type(self) -> Self:

        # TITLE: mandatory text, max 30
        if self.type == LabelType.TITLE:
            if len(self.text) > 30:
                raise ValueError("For TITLE the length of `text` cannot exceed 30 characters.")

        # TEXT: mandatory text, max 50
        elif self.type == LabelType.TEXT:
            if len(self.text) > 50:
                raise ValueError("For TEXT the length of `text` cannot exceed 50 characters.")

        return self


class ComposedElementOut(HomepageElement):
    elements: List[HomepageElementOut] = Field([], description="List of internal labels within the widget")


class HomepageOut(Homepage):
    elements: List[HomepageElementOut | ComposedElementOut] = Field(..., description="Typed blocks for final rendering")


# CLASSES FOR LLM MANAGEMENT

class LLMComposedElement(LLMHomepageElement):
    elements: List[LLMHomepageElement] = Field(..., description="Sub-elements that compose this composite element")


class LLMHomepageIn(Homepage):
    elements: List[LLMHomepageElement | LLMComposedElement] = Field(...,
                                                                    description="List of blocks that compose the homepage")


class LLMHomepageOut(BaseModel):
    elements: List[str | List[str]] = Field(..., description="Raw output from LLM, list of strings or lists of strings")


def validate_homepage_output(homepage_input: Homepage, llm_output: LLMHomepageOut):
    """
    Converts raw LLM output to HomepageOutput:
    - Each simple element becomes a string mapped to the corresponding Pydantic model.
    - Each composite element (COMPOSED) becomes a list of strings mapped to HomepageWidget.
    """
    validated = []
    for element_input, generated in zip(homepage_input.elements, llm_output.elements):
        data = element_input.model_dump()
        if isinstance(generated, list):
            # composite element: generate HomepageWidget with sub-texts
            widget_validated = []
            for widget_input, sub_gen_el in zip(element_input.elements, generated):
                w_data = widget_input.model_dump()
                w_data['text'] = sub_gen_el
                widget_validated.append(HomepageElementOut.model_validate(w_data))
        else:
            # simple element: generate the text field
            data['text'] = generated
            validated.append(HomepageElementOut.model_validate(data))

    result = homepage_input.model_dump()
    result['elements'] = validated
    return HomepageOut.model_validate(result)
