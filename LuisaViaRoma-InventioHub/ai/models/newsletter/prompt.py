import os

from langchain.output_parsers import OutputFixingParser
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)

from models.generation_prompt import create_context_prompt_template, create_few_shot_prompt_template
from models.newsletter.classes import (
    Newsletter,
    NewsletterType,
    LLMNewsletterOut, NewsletterOut,
)
from utils.LLMs import MODELS
from utils.task import GenerationTask

# Specific prompts per newsletter type
# -----------------------------------------------------------------------------
# NOTE: Keep keys aligned with NewsletterType Enum names.
# -----------------------------------------------------------------------------

specific_prompts = {
    NewsletterType.EDITORIAL: (
        """
        GOAL: Generate an **editorial newsletter** that engages readers with storytelling, insights and informational value, in line with the brand tone of voice and able to strengthen the relationship.
    
        ────────────────────────────────────────────────────
        EDITORIAL-SPECIFIC GUIDELINES
        ────────────────────────────────────────────────────
        • **Focus**: storytelling and informational value, relationship-building
        • **Tone**: more educational and consultative, less commercial
        • **Subject line**: based on curiosity, insight, discovery ("How...", "Why...", "The secret of...")
        • **Preheader**: amplifies curiosity or previews informational value
        • **Content elements**: focus on know-how, trends, behind-the-scenes, tutorials
        • **CTA**: soft invites to explore further ("Read more", "Find out how", "Learn more")
        • **Value proposition**: knowledge, inspiration, emotional connection with the brand
        """
    ),
    NewsletterType.PROMO: (
        """
        GOAL: Generate a **promotional newsletter** that drives purchase by highlighting offers, discounts or exclusive benefits and encourages the user to click the CTAs to finalize conversion.
    
        ────────────────────────────────────────────────────
        PROMO-SPECIFIC GUIDELINES
        ────────────────────────────────────────────────────
        • **Focus**: offers, discounts, exclusive benefits, immediate conversion
        • **Tone**: persuasive and action-oriented, sense of urgency
        • **Subject line**: clear benefits, percentage discounts, urgency ("50% OFF", "Last days", "Just for you")
        • **Preheader**: details of the offer or time deadline
        • **Content elements**: highlight discounted products, bundle offers, limited time deals
        • **CTA**: direct toward purchase/conversion ("Buy now", "Take advantage", "Shop now")
        • **Value proposition**: economic savings, exclusivity, limited-time convenience
        • **Urgency/Scarcity**: when appropriate, communicate time or stock limitations
        """
    ),
    NewsletterType.CATEGORY: (
        """
        GOAL: Generate a **category newsletter** that presents a selection of products belonging to a specific category or theme, guiding the user to discover the assortment.
    
        ────────────────────────────────────────────────────
        CATEGORY-SPECIFIC GUIDELINES
        ────────────────────────────────────────────────────
        • **Focus**: showcase of products/services from a specific category
        • **Tone**: balanced between discovery and persuasion, consultative
        • **Subject line**: communicates variety/novelty of the category ("New arrivals", "The collection", "Everything for...")
        • **Preheader**: previews the richness of the assortment or specific highlights
        • **Content elements**: curated selection, product highlights, smart cross-selling
        • **CTA**: oriented toward exploring the assortment ("Discover all", "See collection", "Find out more", "Shop the selection")
        • **Value proposition**: variety, curation, discovery of products aligned with interests
        • **Product presentation**: focus on distinctive features and range of available options
        """
    ),
}


def generate(model, task: GenerationTask):
    uploaded_files = []  # Track any uploaded files for clean-up

    data_input = Newsletter.model_validate(task.data)

    out_cls = LLMNewsletterOut

    # ------------- SYSTEM MESSAGE -------------

    system_prompt = f"""
    You are a senior content marketer specialized in creating **{data_input.type}** newsletters.

    You will receive as input a JSON object with the necessary details for generation.

    {{specific_prompt}}

    ────────────────────────────────────────────────────
    EMAIL MARKETING GUIDELINES
    ────────────────────────────────────────────────────
    • **Deliverability**: avoid spam trigger words, excessive capitalization, too many symbols
    • **Mobile-first**: copy readable on smartphones, clear visual hierarchy
    • **Engagement**: subject line that sparks curiosity/urgency without extreme clickbait
    • **Scannable content**: short headlines, broken paragraphs, implicit bullet points
    • **Value proposition**: every element must provide tangible value to the reader
    • **Conversion path**: logical progression toward the desired action

    ────────────────────────────────────────────────────
    BRAND & TONE GUIDELINES
    ────────────────────────────────────────────────────
    • **Voice**: consistent with brand voice and target segment
    • **Personalization**: when possible, direct and personal language
    • **Credibility**: avoid excessive or too good-to-be-true promises
    • **Inclusivity**: neutral and accessible language
    • **Consistency**: uniform tone among subject, preheader and elements
    • **Brand recall**: reinforce brand recognition without being redundant
    • **Language**: {{language}}

    ────────────────────────────────────────────────────
    PERFORMANCE OPTIMIZATION
    ────────────────────────────────────────────────────
    • **Open rate**: persuasive subject line but not spam-like
    • **Click rate**: clear CTAs and evident value in every element
    • **Conversion rate**: logical path from open to final action
    • **List health**: valuable content that reduces unsubscribe rate
    • **Engagement**: variety in content to maintain interest
    • **Segmentation**: message appropriate for the specific target
    
    {{custom_prompt}}
    
    <!--
    WORKFLOW & SELF-CHECK
    (Internal Chain-of-Thought)

    ────────────────────────────────────────
    MENTAL WORKFLOW (step-by-step)
    ────────────────────────────────────────
    1. Analyze the newsletter type and target audience
    2. Identify the main theme/focus and secondary objectives
    3. Define the strategy for the subject line (curiosity/urgency/benefit)
    4. Plan the preheader as a complement to the subject line
    5. For each element: identify topic, angle, appropriate CTA
    6. Verify character limits
    7. Optimize for deliverability (spam triggers, mobile readability)
    8. Check narrative coherence and progression toward conversion
    9. Ensure that the output is in {{language}}

    ────────────────────────────────────────
    FINAL SELF-CHECK (before returning)
    ────────────────────────────────────────
    1. Does each element strictly comply with the character limits?
    2. Does the subject line encourage opening without being clickbait?
    3. Does the preheader add value to the subject without repeating it?
    4. Are the character limits respected?
    6. Is the tone consistent with the newsletter type?
    7. Are there any problematic spam trigger words?
    8. Correct and uniform language ({{language}})?
    9. Does the progression subject→preheader→elements form a logical path?

    If any point fails, **regenerate** the affected element before delivering.
    -->
    
    """

    system_template = SystemMessagePromptTemplate.from_template(system_prompt)

    # ------------- FEW-SHOT EXAMPLES -------------
    few_shot_template = create_few_shot_prompt_template(
        example_module_path=f"models.{task.content_type.value.lower()}.examples.{data_input.type.value.lower()}",
        input_cls=Newsletter,
        output_cls=out_cls
    )

    # ------------- CONTEXT (images, documents, etc.) -------------
    context_template = create_context_prompt_template(model, task, uploaded_files)

    # ------------- USER MESSAGE -------------
    user_template = HumanMessagePromptTemplate.from_template(
        [
            f"Generate the output by adhering EXACTLY to the following schema:\n{{format_instructions}}\n\n"
            f"IMPORTANT: Reply in {{language}} and ONLY WITH THE REQUESTED STRUCTURE, WITHOUT EXPLANATIONS, EXTRA TEXT OR TRAILING COMMAS.\n\n"
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
        "input_json": data_input.model_dump_json(),
        "format_instructions": parser.get_format_instructions(),
        "language": task.language.complete_name,
        "specific_prompt": specific_prompts.get(data_input.type, ""),
        "number_of_elements": data_input.number_of_elements,
        "custom_prompt": custom_prompt,
    }

    return chain, prompt_inputs, uploaded_files


def validate(task: GenerationTask, generation_result):
    return NewsletterOut.model_validate(task.data | generation_result.model_dump())
