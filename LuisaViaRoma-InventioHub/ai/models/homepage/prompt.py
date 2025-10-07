import os

from langchain.output_parsers import OutputFixingParser
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate

from models.generation_prompt import create_context_prompt_template, create_few_shot_prompt_template
from models.homepage.classes import LLMHomepageOut, Homepage, LLMHomepageIn, validate_homepage_output
from utils.LLMs import MODELS
from utils.task import GenerationTask


def generate(model, task: GenerationTask):
    uploaded_files = []

    data_input = Homepage.model_validate(task.data)

    llm_input = LLMHomepageIn.model_validate(task.data)
    homepage_json = llm_input.model_dump_json()

    out_cls = LLMHomepageOut

    # -------------  SYSTEM  -------------
    system_prompt = f"""
    YOU WILL RECEIVE: a JSON file that lists the micro-texts to create for the homepage of a premium fashion & lifestyle e-commerce. For each element there are:
    • **type**  → TITLE | TEXT | WIDGET | CTA | COMPOSED  
    • **theme** → topic / feature to enhance  
    • **comment** → designer / strategist notes  / product / category

    OBJECTIVE: analyze the JSON and generate brief, incisive copy consistent with the brand's tone of voice. Respect the maximum length indicated for each `type`. If `type == COMPOSED`, return a **list** of strings in the order provided. Do not add extra fields and do not change the input order.

    ────────────────────────────────────────────────────  
    TEXTS TO GENERATE  
    ────────────────────────────────────────────────────  
    ● **TITLE**  
      - Section headline, max **30 characters**  
      - Use a present tense verb or sensory exclamation  
      - Avoid superfluous articles  

    ● **TEXT**  
      - Subtitle / kicker, max **50 characters**  
      - Explain *why* to visit the section  

    ● **WIDGET**  
      - Product/service widget title  
      - Align tone to theme (e.g. "Total denim", "Spa at Home")  

    ● **CTA**  
      - Button micro-copy  
      - Soft action verb in **sentence case** (e.g. "Discover now", "Enter". "Shop now", "Discover the selection")  

    ● **COMPOSED**  
      - List of titles for sub-widgets  
      - Generate **N** strings, where **N = len(COMPOSED.elements)**, respecting the order  

    ────────────────────────────────────────────────────  
    GENERAL GUIDELINES  
    ────────────────────────────────────────────────────  
    • **Voice**: second person singular, inspirational-consultative tone, sensory vocabulary + moderate technical terms  
    • **Brand fit**: premium, inclusive, gender fluid; avoid slang, emojis and multiple exclamation points  
    • **UX copy**: maximum clarity and consistency; each CTA visually corresponds to the action (never "Click here")  
    • **SEO & keyword**: insert keywords naturally; no forced capitals  
    • **Tone consistency**: uniform pronouns, verb tenses and register  
    • **Image integration**: if present, be inspired; cite strong scenes when relevant  
    • **Sustainability & values**: if the *theme* implies it, highlight eco-materials or craftsmanship with micro-storytelling  
    • **Language**: {{language}}
    
    {{custom_prompt}}
    
    <!--
    WORKFLOW & SELF-CHECK  
    (Internal Chain-of-Thought)

    ────────────────────────────────────────  
    MENTAL WORKFLOW (step-by-step)  
    ────────────────────────────────────────  
    1. Read each element: theme, label, comment  
    2. Analyze any images or context documents  
    3. Note primary keywords and visual mood  
    4. For each `type`, select appropriate structure (verb, adjective, benefit)  
    5. Verify lengths (TITLE ≤ 30, TEXT ≤ 50) and consistency with guidelines  
    6. Review tone of voice, keyword density, mobile readability  
    7. Ensure output and order exactly match those of input  
    8. Check that output is in {{language}}  

    ────────────────────────────────────────  
    FINAL SELF-CHECK (before returning)  
    ────────────────────────────────────────  
    1. Does each string respect the character limit?  
    2. Is the copy consistent with theme, label and comment?  
    3. CTA in sentence case and relevant to the action?  
    4. No violation of Brand & UX guidelines?  
    5. Correct and uniform language ({{language}})?  

    If a point fails, **regenerate** the affected part before delivering.
    -->
    """

    system_template = SystemMessagePromptTemplate.from_template(system_prompt)

    # -------------  FEW-SHOT -------------
    category = data_input.device.value.lower() + "_" + data_input.gender.value.lower()

    few_shot_template = create_few_shot_prompt_template(
        example_module_path=f"models.{task.content_type.value.lower()}.examples.{category}",
        input_cls=Homepage,
        output_cls=out_cls
    )

    # -------------  CONTEXT  ----------------
    context_template = create_context_prompt_template(model, task, uploaded_files)

    # -------------  USER  ----------------
    user_template = HumanMessagePromptTemplate.from_template(
        [
            f"Generate the output adhering EXACTLY to the following schema (do not add text, comments or superfluous spaces outside the block):\n{{format_instructions}}\n\n"
            f"IMPORTANT: Respond in {{language}} and ONLY WITH THE REQUIRED STRUCTURE, WITHOUT EXPLANATIONS, ADDITIONAL TEXT OR TRAILING COMMA.\n\n"
            f"INPUT TO ANALYZE: ```json\n{{input_json}}\n```"
        ]
    )

    # --------------------- CUSTOM PROMPT -------------------------
    if task.custom_prompt:
        custom_prompt = f"""
    ────────────────────────────────────────────────────  
    ADDITIONAL INSTRUCTIONS
    ────────────────────────────────────────────────────  
    During the generation consider this additional instructions:
    {task.custom_prompt}
    """
    else:
        custom_prompt = ""

        custom_prompt = ""

    # -------------  CHAT PROMPT ----------
    templates = []

    templates.append(system_template)

    if few_shot_template:
        templates.append(few_shot_template)

    if context_template:
        templates.append(context_template)

    templates.append(user_template)

    chat_prompt = ChatPromptTemplate.from_messages(templates)

    # -------------  PARSER  -------------
    parser = OutputFixingParser.from_llm(
        parser=PydanticOutputParser(pydantic_object=out_cls),
        llm=MODELS.get(os.getenv("AI_FIX_PARSING_MODEL"), model),
        max_retries=int(os.getenv("AI_FIX_PARSING_MAX_RETRIES", 2)),
    )

    # -------------  PIPELINE -------------
    chain = chat_prompt | model | parser

    prompt_inputs = {
        "input_json": homepage_json,
        "format_instructions": parser.get_format_instructions(),
        "language": task.language.complete_name,
        "custom_prompt": custom_prompt,
    }

    return chain, prompt_inputs, uploaded_files


def validate(task: GenerationTask, generation_result):
    return validate_homepage_output(Homepage.model_validate(task.data), generation_result)
