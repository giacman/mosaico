import importlib
import json
from typing import Dict, List

from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain_core.exceptions import OutputParserException
from pydantic import BaseModel, ValidationError

from utils.task import TranslationTask

# --------------- Additional system prompts for "special" tasks ---------------- #
# Nomenclature content_type.type
specific_prompts: Dict[str, str] = {

}


# ------------------------------------------------------------------------------- #


def _get_specific_prompt(task: TranslationTask) -> str:
    """
    Retrieves – if it exists – the specific prompt to insert in the system prompt.
    The choice is made based on:
      1. content_type of the task (e.g. OMNICHANNEL_MESSAGES, …)
      2. optional .type attribute present in the original input
         (e.g. APP, PUSH, WEB etc.)
    You can customize the dispatch logic if you have other criteria.
    """
    # 1) first attempt: use the content_type directly
    if task.content_type.name in specific_prompts:
        return specific_prompts[task.content_type.name]

    # 2) second attempt: use the .type field of the input (if present)
    if isinstance(task.data, BaseModel) and hasattr(task.data, "type"):
        _key = f"{task.content_type.name}.{str(getattr(task.data, "type"))}"
        if _key in specific_prompts:
            return specific_prompts.get(_key, "")

    # 3) no special prompt found
    return ""


# ------------------------------------------------------------------------------- #
#                             MAIN TRANSLATE FUNCTION                                      #
# ------------------------------------------------------------------------------- #
async def translate(model, task: TranslationTask) -> TranslationTask:
    """
    Non-literally translates the textual fields present in `task.data`
    into all languages required in `task.languages`, preserving context
    and meaning. Returns the list of translated data structures
    (one per language, in the order of `task.languages`) and populates
    `task.translations` with the same value.
    """

    # ----------------------------------------------------------------------- #
    # 1) Starting JSON (input for the translator)                            #
    # ----------------------------------------------------------------------- #
    input_json: str = json.dumps(task.data, ensure_ascii=False)

    # ----------------------------------------------------------------------- #
    # 2) System prompt                                                       #
    # ----------------------------------------------------------------------- #
    specific_prompt = _get_specific_prompt(task)

    system_prompt = SystemMessagePromptTemplate.from_template(
        f"""You are an expert editorial content translator specializing in marketing and communications.

        Your task is to translate JSON objects containing various text fields while preserving their 
        structure, tone, intent, and cultural relevance.

        Translation Process (Chain of Thought):

        1. ANALYZE - First, identify all translatable text fields in the JSON
           - Map out which fields contain the **trans_editable** property
           - Note any technical fields that should remain unchanged
           - Understand the content type and communication context

        2. CONTEXTUALIZE - Understand the overall message and purpose
           - What is the primary goal of this content?
           - Who is the target audience?
           - What tone and register are appropriate?

        3. TRANSLATE - For each text field:
           - Consider cultural adaptation, not just literal translation
           - Maintain emotional impact and persuasive power
           - Preserve character limits if implied by field names
           - Keep brand voice consistent

        4. VERIFY - Final quality checks:
           - Is the translation natural and idiomatic in the target language?
           - Does it maintain the original's persuasive intent?
           - Are all text fields translated while preserving JSON structure?
           - Have technical fields been left unchanged?

       {{specific_prompt}}

        Remember: You must return a valid JSON object with the exact same structure as the input,
        where only **trans_editable** fields have been translated.""")

    # ----------------------------------------------------------------------- #
    # 3) Human prompt                                                        #
    # ----------------------------------------------------------------------- #
    human_prompt = HumanMessagePromptTemplate.from_template(
        f"""INPUT JSON to translate:
        ```json
        {{input_json}}
        ```

        Target language: {{language}}

        Instructions:
        1. Translate ONLY fields marked with **trans_editable**
        2. Preserve the exact JSON structure
        3. Keep all technical fields, IDs, and non-textual values unchanged
        4. Apply cultural adaptation where appropriate
        5. Ensure the translation sounds natural in {{language}}

        Return ONLY a valid JSON object with the translated content. Do not include any 
        explanations or comments outside the JSON structure.""")

    # ----------------------------------------------------------------------- #
    # 4) Overall chat prompt                                                 #
    # ----------------------------------------------------------------------- #
    chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])

    # ----------------------------------------------------------------------- #
    # 5) Dynamic parser (if available)                                       #
    # ----------------------------------------------------------------------- #
    class_module = importlib.import_module(
        f"models.{task.content_type.value.lower()}.classes"
    )

    model_cls = getattr(
        class_module,
        f'{task.content_type.value.title().replace("_", "")}Out'
    )

    parser = OutputFixingParser.from_llm(parser=PydanticOutputParser(pydantic_object=model_cls), llm=model,
                                         max_retries=2)

    # ----------------------------------------------------------------------- #
    # 6) Batch input construction                                            #
    # ----------------------------------------------------------------------- #

    batched_inputs: List[dict] = []

    for translation in task.translations:
        batched_inputs.append({
            "input_json": input_json,
            "language": translation.language.complete_name,
            "specific_prompt": specific_prompt,
        })

    # ----------------------------------------------------------------------- #
    # 7) Chain construction                                                  #
    # ----------------------------------------------------------------------- #

    chain = (chat_prompt | model | parser).with_config(task.llm_config.model_dump())

    try:
        translations = await chain.abatch(batched_inputs)

        for i, translation in enumerate(translations):
            task.translations[i].data = translation

    except (ValueError, OutputParserException, ValidationError) as err:
        raise err

    return task



# ------------------------------------------------------------------------------- #
#                             RETRY TRANSLATE FUNCTION                                      #
# ------------------------------------------------------------------------------- #
async def retry_translate(model, task: TranslationTask, retry_custom_prompt: str) -> TranslationTask:

    system_prompt = SystemMessagePromptTemplate.from_template(
        f"""You are an expert editorial content translator specializing in marketing and communications.

        Your task is to *revise* an existing translation of a JSON object,
        applying ONLY the changes specified in the custom prompt, while preserving
        structure, tone, intent and cultural relevance.

        Revision Process:

        1. ANALYZE - First, identify all translatable text fields in the JSON
           - Map out which fields contain the **trans_editable** property
           - Note any technical fields that should remain unchanged
           - Understand the content type and communication context

        2. APPLY INSTRUCTIONS – Read the custom prompt and:
           - For each instruction, identify the fields/texts to update
           - Apply changes to tone, style, terminology and formatting
           - Maintain the original language

        3. VERIFY – Final checks:
           - Does the JSON have the same structure as the input?
           - Have only the textual values in the **trans_editable** fields changed?
           - Is the result consistent with the custom‑prompt instructions?
           - Does the text sound natural and idiomatic in the target language?

        Remember: you must return a valid JSON with the same structure,
        where ONLY the textual values have been modified according to the instructions."""
    )

    human_prompt = HumanMessagePromptTemplate.from_template(
        f"""EXISTING JSON translation:
        ```json
        {{translation}}
        ```

        CUSTOM RETRY INSTRUCTIONS:
        ```txt
        {{retry_custom_prompt}}
        ```

        Instructions:
        1. Keep the original language ({{language}})
        2. Modify ONLY the text fields marked with **trans_editable**
        3. Preserve exactly the original JSON structure
        4. Do not touch technical fields, IDs or non‑text values
        5. Faithfully apply the custom‑prompt instructions
        6. Ensure the result sounds natural in the target language

        Return ONLY a valid JSON with the modified translation,
        without external explanations or comments."""
    )

    chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])

    class_module = importlib.import_module(
        f"models.{task.content_type.value.lower()}.classes"
    )
    model_cls = getattr(
        class_module,
        f'{task.content_type.value.title().replace("_", "")}Out'
    )
    parser = OutputFixingParser.from_llm(
        parser=PydanticOutputParser(pydantic_object=model_cls),
        llm=model,
        max_retries=2
    )

    batched_inputs: List[dict] = []
    for translation in task.translations:
        batched_inputs.append({
            "translation": json.dumps(translation.data, ensure_ascii=False),
            "retry_custom_prompt": retry_custom_prompt,
            "language": translation.language.complete_name,
        })

    chain = (chat_prompt | model | parser).with_config(task.llm_config.model_dump())

    try:
        revisions = await chain.abatch(batched_inputs)
        for i, revision in enumerate(revisions):
            task.translations[i].data = revision
    except (ValueError, OutputParserException, ValidationError) as err:
        raise err

    return task

