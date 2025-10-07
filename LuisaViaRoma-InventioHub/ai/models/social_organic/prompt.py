import importlib
import os
from typing import Dict

from langchain.output_parsers import OutputFixingParser
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate

from models.generation_prompt import create_context_prompt_template, create_few_shot_prompt_template
from models.social_organic.classes import SocialOrganic, Social, SocialOrganicOut
from utils.LLMs import MODELS
from utils.task import GenerationTask

# Specific prompts per social network
# -----------------------------------------------------------------------------
# NOTE: Keep keys aligned with Social Enum names.
# -----------------------------------------------------------------------------

specific_prompts: Dict[Social, str] = {
    Social.INSTAGRAM: """
    OBJECTIVE: Generate organic copy for Instagram posts, aligned with the
    brand's visual and narrative style. The text must be engaging, clear,
    and encourage interaction (likes, comments, shares).

    ────────────────────────────────────────────────────
    INSTAGRAM-SPECIFIC GUIDELINES
    ────────────────────────────────────────────────────
    • **Focus**: visual storytelling, lifestyle, aspiration
    • **Tone**: friendly, conversational, authentic
    • **Structure**: opening hook + body + final CTA
    • **Hashtag**: mix of branded, niche and trending (max 5-8)
    • **Emoji**: strategic use to improve readability and engagement
    • **CTA**: soft and natural ("Tag a friend", "Save for later", "Tell me in the comments")
    • **Length**: concise yet complete, optimized for the “read more” fold
    • **Value**: inspiration, entertainment, practical utility
    """,

    Social.TIKTOK: """
    OBJECTIVE: Produce organic text for a TikTok video that captures attention
    in the first seconds, uses relevant hashtags, and encourages comments
    and shares.

    ────────────────────────────────────────────────────
    TIKTOK-SPECIFIC GUIDELINES
    ────────────────────────────────────────────────────
    • **Focus**: entertainment, trends, virality
    • **Tone**: energetic, direct, Gen Z-friendly
    • **Structure**: powerful hook (0-3 sec) + snackable content
    • **Hashtag**: trending hashtags + challenges + FYP optimization
    • **Language**: appropriate slang, current cultural references
    • **CTA**: challenge-based ("Try it too", "Duet this", "Reply in the comments")
    • **Timing**: in sync with current trends
    • **Value**: entertainment first, information second
    """,

    Social.LINKEDIN: """
    OBJECTIVE: Write organic text for a LinkedIn post that is professional
    and informative, positioning the brand as a thought leader and
    stimulating discussions among professionals.

    ────────────────────────────────────────────────────
    LINKEDIN-SPECIFIC GUIDELINES
    ────────────────────────────────────────────────────
    • **Focus**: thought leadership, professional insights, educational value
    • **Tone**: professional yet accessible, authoritative without pomposity
    • **Structure**: opening statement + reasoned development + actionable conclusion
    • **Hashtag**: industry-specific, professional (max 3-5)
    • **Formatting**: short paragraphs, bullet points for readability
    • **CTA**: networking-oriented ("What do you think?", "Share your experience")
    • **Content**: case studies, industry trends, best practices
    • **Value**: professional growth, networking, industry insights
    """
}


def generate(model, task: GenerationTask):
    uploaded_files = []

    data_input = SocialOrganic.model_validate(task.data)

    class_module = importlib.import_module(
        f"models.{task.content_type.value.lower()}.classes"
    )

    out_cls = getattr(
        class_module,
        f'LLM{task.content_type.value.title().replace("_", "")}{data_input.type.value.replace("_", "")}Out'
    )

    # ------------- SYSTEM MESSAGE -------------
    system_prompt = f"""
    You are a senior content strategist specialized in creating organic
    content for **{data_input.type.value}**.

    You will receive a JSON object as input containing the information needed
    to generate the text.

    {{specific_prompt}}

    ────────────────────────────────────────────────────
    TECHNICAL CONSTRAINTS
    ────────────────────────────────────────────────────

    • **Character limits**: strictly respect the platform limits
    • **Hashtags**: relevant and strategic, no spam
    • **Emoji**: only if consistent with brand voice and platform
    • **Links**: avoid direct links unless explicitly required
    • **Formatting**: optimized for mobile readability
    • **Accessibility**: inclusive and clear language

    ────────────────────────────────────────────────────
    GENERAL GUIDELINES
    ────────────────────────────────────────────────────

    • **Brand consistency**: maintain the brand’s tone of voice and values
    • **Platform native**: adapt the content to platform-specific best practices
    • **Engagement first**: prioritize interaction over impressions
    • **Authenticity**: avoid overly promotional or artificial language
    • **Timing**: consider the ideal publication time
    • **Community**: build relationships, not just reach
    • **Language**: {{language}}

    ────────────────────────────────────────────────────
    ALGORITHMIC OPTIMIZATION
    ────────────────────────────────────────────────────

    • **Dwell time**: content that holds attention
    • **Completion rate**: structure that invites reading to the end
    • **Share-worthy**: elements that encourage sharing
    • **Comment bait**: questions and prompts for discussion (no spam)
    • **Save rate**: useful content users want to keep
    • **Algorithm signals**: optimize for platform-specific signals

    <!--
    WORKFLOW & SELF-CHECK
    (Internal Chain-of-Thought)

    ────────────────────────────────────────
    MENTAL WORKFLOW (step-by-step)
    ────────────────────────────────────────
    1. Analyze the target platform and its quirks
    2. Identify the primary objective (awareness/engagement/conversion)
    3. Define an opening hook to capture attention
    4. Structure the body to maximize retention
    5. Select strategic hashtags for visibility
    6. Insert a natural, platform-appropriate CTA
    7. Verify character limits and formatting
    8. Optimize for the specific algorithm
    9. Ensure consistency with brand voice
    10. Make sure the output is in {{language}}

    ────────────────────────────────────────
    FINAL SELF-CHECK (pre-delivery)
    ────────────────────────────────────────
    1. Does the text respect character limits?
    2. Does the hook capture attention within 3 seconds?
    3. Are hashtags relevant and non-spammy?
    4. Is the tone appropriate for the platform?
    5. Is there a clear yet non-intrusive CTA?
    6. Is the content mobile-friendly?
    7. Does it invite genuine interaction?
    8. Is it consistent with the brand?
    9. Correct language ({{language}})?
    10. Avoids shadow-ban triggers?

    If any check fails, **regenerate** before delivering.
    -->
    """

    system_template = SystemMessagePromptTemplate.from_template(system_prompt)

    # ------------- FEW-SHOT EXAMPLES -------------
    few_shot_template = create_few_shot_prompt_template(
        example_module_path=f"models.{task.content_type.value.lower()}.examples.{data_input.type.value.lower()}",
        input_cls=SocialOrganic,
        output_cls=out_cls
    )

    # ------------- CONTEXT -------------
    context_template = create_context_prompt_template(model, task, uploaded_files)

    # ------------- USER MESSAGE -------------
    user_template = HumanMessagePromptTemplate.from_template(
        [
            f"Generate the output following EXACTLY the schema below:\n{{format_instructions}}\n\n"
            f"IMPORTANT: Answer in {{language}} and ONLY WITH THE REQUESTED STRUCTURE, "
            f"WITHOUT EXPLANATIONS, EXTRA TEXT OR TRAILING COMMAS.\n\n"
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
        "specific_prompt": specific_prompts[data_input.type],
        "input_json": data_input.model_dump_json(),
        "format_instructions": parser.get_format_instructions(),
        "language": task.language.complete_name,
        "custom_prompt": custom_prompt,
    }

    return chain, prompt_inputs, uploaded_files


def validate(task: GenerationTask, generation_result):
    return SocialOrganicOut.model_validate(task.data | generation_result.model_dump())
