import os
from typing import Dict

from langchain.output_parsers import OutputFixingParser
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate

from models.generation_prompt import create_context_prompt_template, create_few_shot_prompt_template
from models.social_paid.classes import SocialPaid, SocialPaidType, SocialPaidOut, LLMSocialPaidOut
from utils.LLMs import MODELS
from utils.task import GenerationTask

# Specific prompts per campaign objective
# -----------------------------------------------------------------------------
# NOTE: Keep keys aligned with SocialPaidType Enum names.
# -----------------------------------------------------------------------------

specific_prompts: Dict[SocialPaidType, str] = {
    SocialPaidType.BRAND_AWARENESS: """
    OBJECTIVE: Create a catchy title, descriptive text and an 
    effective call-to-action for a brand awareness campaign, aimed at 
    increasing brand awareness and engagement.

    ────────────────────────────────────────────────────  
    BRAND AWARENESS SPECIFIC GUIDELINES  
    ────────────────────────────────────────────────────  
    • **Focus**: brand memorability, differentiation, top-of-mind  
    • **Tone**: inspirational, distinctive, brand-centric  
    • **Title**: brand name prominence, unique value proposition  
    • **Text**: emotional storytelling, brand values, "why we exist"  
    • **CTA**: soft engagement ("Learn more", "Discover the story", "Discover the selection")  
    • **KPI focus**: reach, impressions, brand recall lift  
    • **Creative approach**: visual impact, memorable messaging  
    • **Audience**: broad targeting, new-to-brand users  
    """,

    SocialPaidType.CONVERSIONS: """
    OBJECTIVE: Produce a persuasive title, conversion-oriented text 
    and an incisive call-to-action to drive user action 
    (purchase, registration, download).

    ────────────────────────────────────────────────────  
    CONVERSIONS SPECIFIC GUIDELINES  
    ────────────────────────────────────────────────────  
    • **Focus**: immediate action, friction removal, clear value  
    • **Tone**: urgent, benefit-driven, result-oriented  
    • **Title**: main benefit, clear offer, urgency/scarcity  
    • **Text**: social proof, guarantees, overcome objections  
    • **CTA**: direct action ("Buy now", "Sign up free", "Start today")  
    • **KPI focus**: CPA, conversion rate, ROAS  
    • **Psychological triggers**: FOMO, social proof, reciprocity  
    • **Audience**: in-market users, retargeting pools  
    """,

    SocialPaidType.CATALOGUE_SALES: """
    OBJECTIVE: Generate a clear title, informative text and a 
    motivating call-to-action to promote product sales from the 
    catalog, facilitating navigation and purchase.

    ────────────────────────────────────────────────────  
    CATALOGUE SALES SPECIFIC GUIDELINES  
    ────────────────────────────────────────────────────  
    • **Focus**: product discovery, assortment variety, personalization  
    • **Tone**: informative, user-friendly, solution-oriented  
    • **Title**: main category/benefit, "find your..."  
    • **Text**: ease of choice, available filters, wide selection  
    • **CTA**: exploratory ("Browse catalog", "Find yours", "View collection")  
    • **KPI focus**: product views, add-to-cart rate, AOV  
    • **Dynamic elements**: prices, availability, personalization  
    • **Audience**: category browsers, comparison shoppers  
    """,

    SocialPaidType.VIDEO_VIEWS: """
    OBJECTIVE: Write a catchy title, teaser text and a 
    compelling call-to-action to increase views of a 
    promotional video.

    ────────────────────────────────────────────────────  
    VIDEO VIEWS SPECIFIC GUIDELINES  
    ────────────────────────────────────────────────────  
    • **Focus**: curiosity, entertainment value, watch completion  
    • **Tone**: intriguing, emotional, cliffhanger-style  
    • **Title**: provocative question, content preview, "you won't believe..."  
    • **Text**: teaser without spoilers, value promise, video duration  
    • **CTA**: view-oriented ("Watch now", "Play video", "Discover in video")  
    • **KPI focus**: view rate, completion rate, engagement  
    • **Hook elements**: first 3 seconds crucial, thumbnail appeal  
    • **Audience**: video consumers, entertainment seekers  
    """,

    SocialPaidType.PRODUCT_CATALOG: """
    OBJECTIVE: Create a direct title, concise text and a 
    clear call-to-action to invite users to explore the 
    product catalog.

    ────────────────────────────────────────────────────  
    PRODUCT CATALOG SPECIFIC GUIDELINES  
    ────────────────────────────────────────────────────  
    • **Focus**: product range showcase, easy navigation, choice abundance  
    • **Tone**: helpful, organized, benefit-focused  
    • **Title**: clear category, "everything for...", complete solutions  
    • **Text**: search ease, smart filters, recommendations  
    • **CTA**: discovery-driven ("Explore products", "See all", "Browse")  
    • **KPI focus**: catalog engagement, products per session, discovery rate  
    • **User experience**: navigation ease, filter prominence  
    • **Audience**: research phase users, category explorers  
    """
}


def generate(model, task: GenerationTask):
    uploaded_files = []

    # Validate input
    data_input = SocialPaid.model_validate(task.data)

    out_cls = LLMSocialPaidOut

    # ------------- SYSTEM MESSAGE -------------
    system_prompt = f"""
    You are a senior performance marketer specialized in paid social 
    campaigns with **{data_input.type.value.replace("_", " ").lower()}** objective.

    You will receive as input a JSON object with the necessary information to 
    generate title, text and CTA optimized for conversion.

    {{specific_prompt}}

    ────────────────────────────────────────────────────  
    PAID ADS TECHNICAL CONSTRAINTS  
    ────────────────────────────────────────────────────  

    • **Platform policies**: avoid exaggerated claims, medical claims, discrimination  
    • **Quality score**: optimize for relevance, expected CTR, landing page experience  
    • **Ad fatigue**: fresh message that stands out in the feed  
    • **Mobile optimization**: 80%+ traffic is mobile, scannable texts  
    • **Load time**: copy that anticipates landing page experience  

    ────────────────────────────────────────────────────  
    PERFORMANCE MARKETING GUIDELINES  
    ────────────────────────────────────────────────────  

    • **Hook first**: capture attention in 0.5 seconds of scrolling  
    • **Clear value**: main benefit immediately understandable  
    • **Friction removal**: anticipate and resolve common objections  
    • **Trust signals**: credibility elements when possible  
    • **Action oriented**: every element guides toward conversion  
    • **Test-friendly**: structure that allows A/B testing  
    • **Language**: {{language}}

    ────────────────────────────────────────────────────  
    ALGORITHMIC OPTIMIZATION AND BIDDING  
    ────────────────────────────────────────────────────  

    • **Relevance score**: maximize through copy-audience fit  
    • **CTR optimization**: title and visual preview coordination  
    • **Conversion signals**: copy aligned with conversion events  
    • **Audience resonance**: specific language for targeting  
    • **Platform best practices**: Facebook/Instagram/LinkedIn specifics  
    • **Budget efficiency**: copy that maximizes ROAS  
    • **Learning phase**: consistency for algorithm optimization  

    ────────────────────────────────────────────────────  
    PSYCHOLOGICAL TRIGGERS & PERSUASION  
    ────────────────────────────────────────────────────  

    • **Scarcity**: when appropriate, time/quantity limits  
    • **Social proof**: implicit through inclusive language  
    • **Authority**: expertise and category leadership  
    • **Reciprocity**: value-first approach  
    • **Consistency**: align with user journey stage  
    • **Liking**: brand personality that resonates  
    
    {{custom_prompt}}
    
    <!--
    WORKFLOW & SELF-CHECK  
    (Internal Chain-of-Thought)

    ────────────────────────────────────────  
    MENTAL WORKFLOW (step-by-step)  
    ────────────────────────────────────────  
    1. Identify campaign objective and main KPI  
    2. Analyze target audience and pain points  
    3. Define main hook for title (benefit/urgency/curiosity)  
    4. Structure text to support and expand title promise  
    5. Select most action-oriented CTA verb for objective  
    6. Verify logical flow title→text→CTA  
    7. Optimize for platform algorithms and policies  
    8. Check strict character limits  
    9. Eliminate friction words and jargon  
    10. Finalize in target {{language}}  

    ────────────────────────────────────────  
    PERFORMANCE CHECKLIST (pre-launch)  
    ────────────────────────────────────────
    1. Does the text respect character limits?    
    2. Message aligned with campaign objective?  
    3. Copy policy-compliant (no false claims)?  
    4. Mobile-first readability verified?  
    5. Appropriate psychological triggers inserted?  
    6. Landing page experience anticipated?  
    7. A/B test potential considered?  
    8. Correct target language ({{language}})?  

    If a check fails, **optimize** before delivering.
    -->
    """

    system_template = SystemMessagePromptTemplate.from_template(system_prompt)

    # ------------- FEW-SHOT EXAMPLES -------------

    few_shot_template = create_few_shot_prompt_template(
        example_module_path=f"models.{task.content_type.value.lower()}.examples.{data_input.type.value.lower()}",
        input_cls=SocialPaid,
        output_cls=out_cls
    )

    # ------------- CONTEXT -------------
    context_template = create_context_prompt_template(model, task, uploaded_files)

    # ------------- USER MESSAGE -------------
    user_template = HumanMessagePromptTemplate.from_template(
        [
            f"IMPORTANT: Generate output respecting EXACTLY the following JSON schema (without additional text):\n{{format_instructions}}\n",
            f"\nIMPORTANT: Respond ONLY with the required structure, without explanations or comments.\n",
            f"\nIMPORTANT: Respond in {{language}}.\n",
            f"\nINPUT: ```json\n{{input_json}}\n```"
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

    prompt_inputs = {
        "specific_prompt": specific_prompts.get(data_input.type, ""),
        "input_json": data_input.model_dump_json(),
        "format_instructions": parser.get_format_instructions(),
        "language": task.language.complete_name,
        "custom_prompt": custom_prompt,
    }

    chain = chat_prompt | model | parser

    return chain, prompt_inputs, uploaded_files


def validate(task: GenerationTask, generation_result: LLMSocialPaidOut):
    return SocialPaidOut.model_validate(task.data | generation_result.model_dump())
