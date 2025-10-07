import importlib
import os
from typing import Dict

from langchain.output_parsers import OutputFixingParser
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate

from models.generation_prompt import create_context_prompt_template, create_few_shot_prompt_template
from models.marketing_campaign.classes import (
    MarketingCampaign,
    CampaignType,
    MarketingCampaignOut
)
from utils.LLMs import MODELS
from utils.task import GenerationTask

# Specific prompts per marketing campaign type
specific_prompts: Dict[CampaignType, str] = {
    CampaignType.AFFILIATION_LANDING: """
    OBJECTIVE: Generate a persuasive headline and body copy for an affiliate landing page,
    aimed at maximizing the conversion rate of users coming from external channels.
    """,
    CampaignType.AFFILIATION_BANNER: """
    OBJECTIVE: Create headline, body copy and CTA for affiliate banners,
    optimized to attract clicks and drive traffic to the offer.
    """,
    CampaignType.PROGRAMMATIC_BANNER: """
    OBJECTIVE: Write headline, body copy and call-to-action for programmatic banners,
    aligned with the target audience.
    """
}


def generate(model, task: GenerationTask):
    uploaded_files = []

    # Validate input
    data_input = MarketingCampaign.model_validate(task.data)

    # Determine output model class based on campaign type
    class_module = importlib.import_module(
        f"models.{task.content_type.value.lower()}.classes"
    )

    out_cls = getattr(
        class_module,
        f'LLM{task.content_type.value.title().replace("_", "")}{data_input.type.value.replace("_", "")}Out'
    )

    # ------------- SYSTEM MESSAGE -------------
    system_prompt = f"""
    You are a digital marketer specialized in {data_input.type.value.replace('_', ' ').lower()} marketing campaigns.

    You will receive a JSON object containing the campaign details.

    {{specific_prompt}}

    ──────────────────────────────────────────
    TECHNICAL CONSTRAINTS:
    ──────────────────────────────────────────
    ● **TITLE**: MAX {{title_max_length}} characters (spaces included)
    ● **TEXT**: MAX {{text_max_length}} characters (spaces included)
    ● **CTA**: MAX {{cta_max_length}} characters (spaces included)

    ────────────────────────────────────────────────────  
    PERFORMANCE MARKETING GUIDELINES  
    ────────────────────────────────────────────────────  
    • **Conversion**: every element must push toward the final action; remove friction and doubts  
    • **Urgency & Scarcity**: when appropriate, communicate time or stock limitations  
    • **Value proposition**: always clear and quantifiable (discount %, time saved, benefit obtained)  
    • **Target alignment**: language and benefits calibrated to the specific audience  
    • **Mobile optimization**: copy must be readable and impactful even on smartphones  
    • **Platform specific**: adapt the register to the platform (social, display, search)  

    ────────────────────────────────────────────────────  
    BRAND & TONE GUIDELINES  
    ────────────────────────────────────────────────────  
    • **Voice**: professional yet accessible, results-oriented  
    • **Register**: direct and persuasive without being aggressive  
    • **Credibility**: avoid unrealistic or too-good-to-be-true promises  
    • **Inclusivity**: neutral language accessible to diverse demographics  
    • **Compliance**: respect advertising regulations and avoid unsupported medical/financial claims  
    • **Brand consistency**: maintain coherence with the company voice & tone  
    • **Language**: {{language}}  

    {{custom_prompt}}
    
    <!--
    WORKFLOW & SELF-CHECK  
    (Internal Chain-of-Thought)

    ────────────────────────────────────────  
    STEP-BY-STEP MENTAL WORKFLOW  
    ────────────────────────────────────────  
    1. Analyze the campaign type and the target audience  
    2. Identify the main value proposition and secondary benefits  
    3. Examine the specific offer and any time/stock limitations  
    4. Select appropriate power words and emotional triggers  
    5. Define the information hierarchy (what to say first/after)  
    6. Check strict char limits (TITLE ≤ {{title_max_length}}, TEXT ≤ {{text_max_length}}, CTA ≤ {{cta_max_length}})  
    7. Optimize for conversion rate and user experience  
    8. Check compliance and brand alignment  
    9. Ensure the output is in {{language}}  

    ────────────────────────────────────────  
    FINAL SELF-CHECK (before delivering)  
    ────────────────────────────────────────  
    1. Does each element strictly respect the character limit?  
    2. Is the value proposition clear and compelling?  
    3. Is the CTA specific and action-oriented?  
    4. Is the messaging consistent with the campaign type and target?  
    5. Are there no exaggerated or problematic claims?  
    6. Is the tone appropriate for the platform?  
    7. Correct and uniform language ({{language}})?  
    8. Do title + text + cta together form a logical persuasive path?  

    If any point fails, **regenerate** the affected element before delivering.
    -->
    """

    system_template = SystemMessagePromptTemplate.from_template(system_prompt)

    # ------------- FEW-SHOT EXAMPLES -------------
    few_shot_template = create_few_shot_prompt_template(
        example_module_path=f"models.{task.content_type.value.lower()}.examples.{data_input.type.value.lower()}",
        input_cls=MarketingCampaign,
        output_cls=out_cls
    )

    # ------------- CONTEXT -------------
    context_template = create_context_prompt_template(model, task, uploaded_files)

    # ------------- USER MESSAGE -------------
    user_template = HumanMessagePromptTemplate.from_template(
        [
            f"Generate the output adhering EXACTLY to the following schema (do not add text, comments or extra spaces outside the block):\n{{format_instructions}}\n\n"
            f"IMPORTANT: Reply in {{language}} and ONLY WITH THE REQUIRED STRUCTURE, WITHOUT EXPLANATIONS, ADDITIONAL TEXT OR TRAILING COMMAS.\n\n"
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


    # ------------- CHAT PROMPT PIPELINE -------------
    templates = []

    templates.append(system_template)

    if few_shot_template:
        templates.append(few_shot_template)

    if context_template:
        templates.append(context_template)

    templates.append(user_template)

    chat_prompt = ChatPromptTemplate.from_messages(templates)

    # ------------- OUTPUT PARSER -------------
    parser = OutputFixingParser.from_llm(
        parser=PydanticOutputParser(pydantic_object=out_cls),
        llm=MODELS.get(os.getenv("AI_FIX_PARSING_MODEL"), model),
        max_retries=int(os.getenv("AI_FIX_PARSING_MAX_RETRIES", 2)),
    )

    # ------------- INVOCATION -------------
    chain = chat_prompt | model | parser

    prompt_inputs = {
        "title_max_length": data_input.title_char_limit if data_input.title_char_limit > 0 else "+inf",
        "text_max_length": data_input.text_char_limit if data_input.text_char_limit > 0 else "+inf",
        "cta_max_length": data_input.cta_char_limit if data_input.cta_char_limit > 0 else "+inf",
        "input_json": data_input.model_dump_json(),
        "format_instructions": parser.get_format_instructions(),
        "language": task.language.complete_name,
        "specific_prompt": specific_prompts.get(data_input.type, ''),
        "custom_prompt": custom_prompt,
    }

    return chain, prompt_inputs, uploaded_files


def validate(task: GenerationTask, generation_result):
    return MarketingCampaignOut.model_validate(task.data | generation_result.model_dump())
