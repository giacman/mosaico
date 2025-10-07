from typing import List

from pydantic import BaseModel, Field, computed_field

########## Classes to manage input coming from the platform and input that will be given to AI

class Subparagraph(BaseModel):
    orderid01_title: str = Field(..., json_schema_extra={"trans_editable": True},
                       description="Concise and descriptive title for the H3 paragraph, useful for introducing the section content.")
    orderid12_content_description: str = Field("",
                                     description="Description or additional guidelines for writing the paragraph content. May include context, style, and distinctive features.")
    orderid13_mention_list: List[str] = Field([],
                                    description="List of products or brands that must be mentioned in the paragraph, identified by name. Useful for linking editorial content and catalog.")


class Paragraph(Subparagraph):
    orderid20_subparagraphs: List[Subparagraph] = Field([],
                                              description="List of H3 sub-paragraphs that explore different aspects or sub-themes of the main H2 paragraph.")


class LLMEditorialIn(BaseModel):
    orderid01_theme: str = Field(...,
                       description="Editorial category of the article (e.g., 'Fashion', 'Technology', etc.). Used to thematically frame the content.")
    orderid02_meta_title: str = Field(...,
                            description="Search engine optimized title (meta title), must be catchy and contain strategic keywords.")
    orderid03_meta_description: str = Field(...,
                                  description="Concise description for the meta tag description. Summarizes main content from an SEO perspective.")
    orderid04_keywords: List[str] = Field(...,
                                description="Main keywords (short-tail) to integrate into the text for SEO positioning.")
    orderid05_long_keywords: List[str] = Field([],
                                     description="Long-tail keywords, useful for answering specific user searches.")
    orderid06_user_questions: List[str] = Field([], description="Frequently asked questions by users on the topic. Content must include targeted answers.")
    orderid07_title: str = Field(..., json_schema_extra={"trans_editable": True},
                       description="Main title of the article, visible to the user. Must be clear, engaging and informative.")
    orderid08_excerpt: str = Field(...,
                         description="Brief summary of the article, used as excerpt in preview contexts (e.g., homepage, cards, etc.).")
    orderid10_paragraphs: List[Paragraph] = Field(...,
                                        description="Structured list of H2 paragraphs of the article, each with possible H3 sub-paragraphs for depth.")


class LLMSubparagraph(BaseModel):
    orderid02_text: str = Field(..., json_schema_extra={"trans_editable": True},
                      description="Paragraph text. Must be fluid, relevant to the theme and without title.")
    orderid03_style_suggestions: List[str] = Field([], json_schema_extra={"trans_editable": True},
                                         description="Style suggestions on what and how to wear it")


class LLMParagraph(LLMSubparagraph):
    orderid20_subparagraphs: List[LLMSubparagraph] = Field([],
                                                 description="List of H3 sub-paragraphs (text only) that constitute the depth explorations of the H2 paragraph.")


class LLMEditorialOut(BaseModel):
    orderid09_introduction: str = Field(...,
                              description="Introduction to open the article. Must clearly summarize the main themes.")
    orderid10_paragraphs: List[LLMParagraph] = Field(...,
                                           description="List of H2 paragraphs with their respective generated H3 sub-paragraphs. Each block must be coherent and well-structured.")


class Editorial(LLMEditorialIn):
    orderid20_CTAs: List[str] = Field([], description="List of CTAs linked to the article")
    orderid21_related_articles: List[str] = Field([],
                                        description="List of URLs or identifiers (e.g., slugs) of related articles to propose as additional reading.")
    orderid22_tags: List[str] = Field([],
                            description="Tags used to identify and classify the article in the editorial system (e.g., project, theme, format).")
    orderid23_url: str = Field("", description="Final URL of the web page where the article will be published.")


class SubparagraphOut(Subparagraph, LLMSubparagraph):
    pass


class ParagraphOut(SubparagraphOut):
    orderid20_subparagraphs: List[SubparagraphOut] = Field([])


class EditorialOut(Editorial):
    orderid09_introduction: str = Field(..., json_schema_extra={"trans_editable": True},
                              description="Introduction to open the article. Must clearly summarize the main themes.")
    orderid10_paragraphs: List[ParagraphOut] = Field(...)

    @computed_field
    @property
    def index(self) -> List[str]:
        return [p.orderid01_title for p in self.orderid10_paragraphs]


def validate_editorial_output(ed_input: Editorial, llm_output: LLMEditorialOut):
    input_dict = ed_input.model_dump()
    merged_par = []
    for input_paragraph, llm_paragraph in zip(ed_input.orderid10_paragraphs, llm_output.orderid10_paragraphs):
        merged_sub = []
        for input_sub, llm_sub in zip(input_paragraph.orderid20_subparagraphs, llm_paragraph.orderid20_subparagraphs):
            merged_sub.append(input_sub.model_dump() | llm_sub.model_dump())
        merged_par.append(input_paragraph.model_dump() | llm_paragraph.model_dump())
        merged_par[-1]["orderid20_subparagraphs"] = merged_sub
    llm_dict = llm_output.model_dump()
    llm_dict["orderid10_paragraphs"] = merged_par
    return EditorialOut.model_validate(input_dict | llm_dict)
