import importlib
import os
from typing import Dict

from langchain.output_parsers import OutputFixingParser
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate

from models.generation_prompt import create_context_prompt_template, create_few_shot_prompt_template
from models.omni_banner.classes import OmniBanner, OmniBannerTaskType, OmniBannerOut
from utils.LLMs import MODELS
from utils.task import GenerationTask

# Specific prompts per banner type
# -----------------------------------------------------------------------------
# NOTE: Keep keys aligned with OmniBannerTaskType Enum names.
# -----------------------------------------------------------------------------

specific_prompts: Dict[OmniBannerTaskType, str] = {
    OmniBannerTaskType.SCENES: (
        """
        OBJECTIVE: Generate **micro-texts for omnichannel banner scenes** that capture 
        the brand essence through incisive and evocative messages, perfectly 
        integrated with high fashion visual content to create immediate emotional impact.

        ────────────────────────────────────────────────────  
        SPECIFIC SCENES GUIDELINES  
        ────────────────────────────────────────────────────  
        • **Focus**: visual storytelling, emotional branding, image accompaniment  
        • **Tone**: elegant, aspirational, evocative without being verbose  
        • **Text**: messages that amplify visual impact and create emotional connection  
        • **CTA**: sophisticated invitations to exploration ("Discover", "Explore", "Immerse")  
        • **Value proposition**: premium experience, aspirational lifestyle, emotional connection  
        • **Visual synergy**: texts that complement without competing with visual elements  
        """
    ),

    OmniBannerTaskType.DYBANNERS_APP: (
        """
        OBJECTIVE: Create **dynamic copy for personalized in-app banners** that convey 
        a sense of exclusivity and VIP access, stimulating immediate interaction through 
        messages that adapt to user behavior.

        ────────────────────────────────────────────────────  
        SPECIFIC DYBANNERS_APP GUIDELINES  
        ────────────────────────────────────────────────────  
        • **Focus**: personalization, VIP exclusivity, user behaviors, mobile-first  
        • **Tone**: urgent but sophisticated, exclusive, tech-savvy  
        • **Title**: headlines that communicate privileged access and exclusive value  
        • **Text**: messages that reinforce luxury perception and action urgency  
        • **CTA**: immediate actions emphasizing exclusivity ("Access now", "Reserved for you")  
        • **Value proposition**: early access, exclusive drops, membership privileges  
        • **Personalization**: language that recognizes individual user value  
        """
    ),

    OmniBannerTaskType.DYBANNERS_SITE_CATALOG: (
        """
        OBJECTIVE: Produce **headlines and copy for catalog banners** that highlight 
        product categories and collections, creating desirability and sense of urgency 
        while guiding exploration of the assortment.

        ────────────────────────────────────────────────────  
        SPECIFIC DYBANNERS_SITE_CATALOG GUIDELINES  
        ────────────────────────────────────────────────────  
        • **Focus**: category highlighting, product discovery, collection showcase  
        • **Tone**: curatorial, authoritative, trend-aware, premium, editorial
        • **Title**: category names that evoke desire and completeness of offering  
        • **Text**: descriptions that balance information and persuasion for exploration  
        • **CTA**: invitations to discover assortment ("Discover all", "See collection", "Shop Now")  
        • **Value proposition**: expert curation, premium variety, trend discovery  
        • **Catalog navigation**: facilitate orientation and deepening by category  
        """
    ),

    OmniBannerTaskType.DYBANNERS_SITE_LEVEL: (
        """
        OBJECTIVE: Write **texts for dynamic site-wide banners** with differentiated 
        messages for new and returning users, focused on personalized discovery 
        and strengthening the bond with the brand.

        ────────────────────────────────────────────────────  
        SPECIFIC DYBANNERS_SITE_LEVEL GUIDELINES  
        ────────────────────────────────────────────────────  
        • **Focus**: brand relationship, user journey stage, personalized discovery  
        • **Tone**: welcoming for new users, grateful for returning, always premium  
        • **Text**: messages that recognize existing relationship or invite discovery  
        • **CTA**: actions that strengthen brand connection and personalize experience  
        • **Value proposition**: personalized journey, brand loyalty, tailored discovery  
        • **User segmentation**: language adapted to level of brand familiarity  
        """
    ),

    OmniBannerTaskType.DYCAMPAIGNS_PROD_PAGE: (
        """
        OBJECTIVE: Generate **hyper-targeted copy for product pages** that valorize 
        distinctive product characteristics and accompany the user toward 
        purchase decision highlighting uniqueness and quality.

        ────────────────────────────────────────────────────  
        SPECIFIC DYCAMPAIGNS_PROD_PAGE GUIDELINES  
        ────────────────────────────────────────────────────  
        • **Focus**: product uniqueness, purchase decision, distinctive features  
        • **Tone**: consultative, expert, confidence-building, specific  
        • **Text**: messages that highlight craftsmanship, materials, product exclusivity  
        • **Value proposition**: superior quality, artisanship, lasting investment  
        • **Purchase intent**: remove friction and doubts, guide toward checkout  
        • **Product storytelling**: create emotional connection with specific object  
        """
    ),

    OmniBannerTaskType.LVR_STORIES: (
        """
        OBJECTIVE: Conceive **narrative fragments for stories** in editorial style 
        that accompany high fashion visual content with evocative language, 
        creating emotional engagement and inviting exploration.

        ────────────────────────────────────────────────────  
        SPECIFIC LVR_STORIES GUIDELINES  
        ────────────────────────────────────────────────────  
        • **Focus**: editorial storytelling, visual harmony, emotional engagement  
        • **Tone**: narrative, evocative, artistic, sophisticated  
        • **Text**: micro-stories that create atmosphere and amplify visual impact  
        • **CTA**: soft invitations to deepening ("Discover more", "Read all")  
        • **Value proposition**: inspiration, behind-the-scenes, fashion insight  
        • **Content flow**: narrative that develops through multiple stories  
        """
    ),

    OmniBannerTaskType.RIBBON: (
        """
        OBJECTIVE: Provide **texts for persistent ribbons** that communicate 
        promotions, exclusive benefits or special initiatives maintaining sophisticated 
        tone and non-invasive navigation.

        ────────────────────────────────────────────────────  
        SPECIFIC RIBBON GUIDELINES  
        ────────────────────────────────────────────────────  
        • **Focus**: persistent messaging, promotions, site-wide benefits  
        • **Tone**: informative but elegant, non-invasive, benefit-focused  
        • **Text**: concise communication of offers or always visible advantages  
        • **Text_and_cta**: integrated message that includes action naturally  
        • **Value proposition**: convenience, ongoing benefits, transparent value  
        • **User experience**: do not interfere with main navigation  
        """
    ),

    OmniBannerTaskType.POP_UP: (
        """
        OBJECTIVE: Generate **persuasive copy for pop-up modals** aimed at 
        lead capture or promotion of time-sensitive offers, capturing 
        immediate attention and guiding toward action.

        ────────────────────────────────────────────────────  
        SPECIFIC POP_UP GUIDELINES  
        ────────────────────────────────────────────────────  
        • **Focus**: immediate attention, lead capture, time-sensitive offers  
        • **Tone**: persuasive but respectful, value-focused, urgency without pressure  
        • **Text**: messaging that immediately communicates value and action benefit  
        • **CTA**: direct actions that emphasize convenience and immediate value  
        • **Value proposition**: exclusive access, immediate benefit, limited time value  
        • **Conversion optimization**: minimize friction, maximize perceived value  
        """
    ),
}


def generate(model, task: GenerationTask):
    uploaded_files = []

    data_input = OmniBanner.model_validate(task.data)

    class_module = importlib.import_module(
        f"models.{task.content_type.value.lower()}.classes"
    )

    out_cls = getattr(
        class_module,
        f'LLM{task.content_type.value.title().replace("_", "")}{data_input.type.value.replace("_", "")}Out'
    )

    # ------------- SYSTEM MESSAGE -------------
    system_prompt = f"""
    You are a copywriter specialized in **omnichannel banners for luxury fashion**,
    expert in creating copy for the type **{data_input.type.value.lower()}**.

    You will receive as input a JSON object with the necessary details for generating 
    micro-texts for banners destined for different touchpoints of the digital experience.

    {{specific_prompt}}

    ────────────────────────────────────────────────────  
    BANNER DESIGN & UX GUIDELINES  
    ────────────────────────────────────────────────────  
    • **Visual hierarchy**: texts that support and do not compete with visual elements  
    • **Responsive design**: optimal readability on mobile, tablet, desktop  
    • **Attention economy**: messages that capture attention without being invasive  
    • **Loading speed**: concise copy that does not impact performance  
    • **User journey**: each banner must logically guide to the next step  
    • **Brand consistency**: uniform voice across all touchpoints  

    ────────────────────────────────────────────────────  
    BRAND & TONE GUIDELINES  
    ────────────────────────────────────────────────────  
    • **Voice**: luxury fashion, sophisticated but accessible, aspirational  
    • **Personalization**: language that recognizes individual user value  
    • **Credibility**: maintainable promises, no overselling, premium authenticity  
    • **Inclusivity**: language that welcomes different styles and preferences  
    • **Consistency**: coherent tone across all banner types  
    • **Brand recognition**: reinforce identity without being redundant  
    • **Language**: {{language}}

    ────────────────────────────────────────────────────  
    PERFORMANCE OPTIMIZATION  
    ────────────────────────────────────────────────────  
    • **Click-through rate**: clear CTAs that communicate immediate value  
    • **Conversion rate**: logical path from awareness to action  
    • **User engagement**: content that invites interaction and exploration  
    • **Brand recall**: memorable messages that reinforce positioning  
    • **Customer lifetime value**: copy that builds lasting relationships  
    • **Omnichannel coherence**: consistency across all channels  
    
    {{custom_prompt}}
    
    <!--
    WORKFLOW & SELF-CHECK  
    (Internal Chain-of-Thought)

    ────────────────────────────────────────────────────  
    MENTAL WORKFLOW (step-by-step)  
    ────────────────────────────────────────────────────  
    1. Analyze banner type and specific usage context  
    2. Identify target audience and customer journey phase  
    3. Define key message and appropriate emotional triggers  
    4. Plan informational hierarchy (title→text→cta)  
    5. Optimize for specific device/placement  
    6. Verify rigorous character limits  
    7. Ensure coherence with luxury brand voice  
    8. Check logical flow toward conversion  
    9. Validate that output is in {{language}}

    ────────────────────────────────────────────────────  
    FINAL SELF-CHECK (before returning)  
    ────────────────────────────────────────────────────  
    1. Does each field rigorously respect character limits?  
    2. Is the message appropriate for the banner type?  
    3. Do title and text have clear informational hierarchy?  
    4. Is CTA actionable and coherent with objective?  
    5. Is tone luxury but accessible?  
    6. Are there no conflicts with UX best practices?  
    7. Correct and uniform language ({{language}})?  
    8. Does copy support omnichannel customer journey?  

    If a point fails, **regenerate** the affected element before delivering.
    -->
    """

    system_template = SystemMessagePromptTemplate.from_template(system_prompt)

    # -------------  FEW-SHOT -------------
    few_shot_template = create_few_shot_prompt_template(
        example_module_path=f"models.{task.content_type.value.lower()}.examples.{data_input.type.value.lower()}",
        input_cls=OmniBanner,
        output_cls=out_cls
    )

    # -------------  CONTEXT  ----------------
    context_template = create_context_prompt_template(model, task, uploaded_files)

    # -------------  USER  ----------------
    user_template = HumanMessagePromptTemplate.from_template(
        [
            f"Generate the output following EXACTLY the following schema (do not add text, comments or superfluous spaces outside the block):\n{{format_instructions}}\n\n"
            f"IMPORTANT: Respond ONLY with the required structure, without explanations, additional text or trailing comma.\n\n"
            f"IMPORTANT: Respect character limits for each field.\n\n"
            f"IMPORTANT: Respond in {{language}}\n\n"
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

    # ----------  INVOCATION -------------
    prompt_inputs = {
        "specific_prompt": specific_prompts[data_input.type],
        "input_json": data_input.model_dump_json(),
        "format_instructions": parser.get_format_instructions(),
        "language": task.language.complete_name,
        "task_type": data_input.type.value,
        "custom_prompt": custom_prompt,
    }

    return chain, prompt_inputs, uploaded_files


def validate(task: GenerationTask, generation_result):
    return OmniBannerOut.model_validate(task.data | generation_result.model_dump())
