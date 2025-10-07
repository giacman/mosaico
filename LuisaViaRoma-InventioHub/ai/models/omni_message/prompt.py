import importlib
import os
from typing import Dict

from langchain.output_parsers import OutputFixingParser
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate

from models.generation_prompt import create_context_prompt_template, create_few_shot_prompt_template
from models.omni_message.classes import OmniMessage, OmniMessageTaskType, OmniMessageOut
from utils.LLMs import MODELS
from utils.task import GenerationTask

# Specific prompts per message type
# -----------------------------------------------------------------------------
# NOTE: Keep keys aligned with OmniMessageTaskType Enum names.
# -----------------------------------------------------------------------------

specific_prompts: Dict[OmniMessageTaskType, str] = {
    OmniMessageTaskType.APP: (
        """
        OBJECTIVE: Generate **omnichannel in-app messages** that capture user 
        attention during navigation, communicating exclusive value and stimulating 
        immediate interaction with luxury and personalized messages.

        ────────────────────────────────────────────────────  
        SPECIFIC GUIDELINES FOR APP MESSAGES  
        ────────────────────────────────────────────────────  
        • **Focus**: in-app engagement, contextual messaging, seamless UX integration  
        • **Tone**: sophisticated yet direct, premium non-invasive, contextually relevant  
        • **Title**: concise headlines that capture attention without disturbing the experience  
        • **Text**: messages that add value to the user's current session  
        • **CTA**: actions that integrate naturally into the navigation flow  
        • **Value proposition**: enhanced experience, personalized discovery, exclusive access  
        • **User experience**: messaging that enriches rather than interrupts  
        • **Timing relevance**: content appropriate to the moment and context of use  
        """
    ),

    OmniMessageTaskType.PUSH: (
        """
        OBJECTIVE: Create **omnichannel push notifications** that cut through 
        daily digital noise, stimulating re-engagement with time-sensitive messages 
        and exclusive value that embody luxury brand positioning.

        ────────────────────────────────────────────────────  
        SPECIFIC GUIDELINES FOR PUSH NOTIFICATIONS  
        ────────────────────────────────────────────────────  
        • **Focus**: re-engagement, time-sensitive offers, cutting through digital noise  
        • **Tone**: urgent yet elegant, exclusive appeal, immediate value communication  
        • **Title**: headlines that immediately communicate exclusivity and relevance  
        • **Text**: messages that create FOMO and desire while maintaining sophistication  
        • **CTA**: actions that emphasize immediate action and seamless app return  
        • **Value proposition**: limited-time access, exclusive previews, personalized alerts  
        • **Notification strategy**: optimal timing for maximum open rates  
        • **Personalization**: leveraging user behavior and preferences for relevance  
        """
    ),
}


def generate(model, task: GenerationTask):
    uploaded_files = []

    # ------------- INPUT VALIDATION -------------
    data_input = OmniMessage.model_validate(task.data)

    class_module = importlib.import_module(
        f"models.{task.content_type.value.lower()}.classes"
    )

    out_cls = getattr(
        class_module,
        f'LLM{task.content_type.value.title().replace("_", "")}{data_input.type.value.replace("_", "")}Out'
    )

    # ------------- SYSTEM MESSAGE -------------
    system_prompt = f"""
    You are a copywriter specialized in **omnichannel messaging for luxury fashion**,
    expert in creating copy for the **{data_input.type.value.lower()}** type.

    You will receive as input a JSON object with the details necessary for generating 
    micro-texts for messages destined for different touchpoints of the mobile experience.

    {{specific_prompt}}

    ────────────────────────────────────────────────────  
    MOBILE MESSAGING & UX GUIDELINES  
    ────────────────────────────────────────────────────  
    • **Attention economy**: messages that compete with infinite digital distractions  
    • **Mobile-first design**: optimization for quick reading on smartphones  
    • **User permission respect**: content that justifies interrupting the user  
    • **Notification fatigue**: avoid over-messaging that leads to opt-out  
    • **Contextual relevance**: timing and content appropriate to the moment of use  
    • **Brand permission**: every message must reinforce rather than erode trust  

    ────────────────────────────────────────────────────  
    BRAND & TONE GUIDELINES  
    ────────────────────────────────────────────────────  
    • **Voice**: luxury fashion, sophisticated yet accessible, premium positioning  
    • **Personalization**: messages that recognize individual preferences and behaviors  
    • **Credibility**: maintainable promises, no clickbait, authentic premium value  
    • **Exclusivity communication**: language that reinforces the user's VIP status  
    • **Emotional triggers**: desires, aspiration, FOMO managed with elegance  
    • **Brand recall**: consistency across all touchpoints for brand recognition  
    • **Language**: {{language}}

    ────────────────────────────────────────────────────  
    PERFORMANCE OPTIMIZATION  
    ────────────────────────────────────────────────────  
    • **Open rates**: titles that stimulate curiosity without being misleading  
    • **Click-through rates**: CTAs that communicate clear value and immediate benefit  
    • **Conversion rates**: messaging that guides seamlessly toward desired action  
    • **Retention impact**: content that strengthens brand relationship  
    • **Opt-out prevention**: balance between frequency, relevance and perceived value  
    • **Cross-channel coherence**: consistency with other marketing touchpoints  
    
    {{custom_prompt}}
    
    <!--
    WORKFLOW & SELF-CHECK  
    (Internal Chain-of-Thought)

    ────────────────────────────────────────────────────  
    MENTAL WORKFLOW (step-by-step)  
    ────────────────────────────────────────────────────  
    1. Analyze the message type and specific context (app vs push)  
    2. Identify user intent and customer journey phase  
    3. Define key message and appropriate emotional hooks  
    4. Optimize for mobile reading patterns and attention spans  
    5. Plan title→text→cta flow for maximum impact  
    6. Verify extremely strict character limits for mobile display  
    7. Ensure brand voice consistency with luxury positioning  
    8. Check timing and context appropriateness  
    9. Validate that output is in {{language}}

    ────────────────────────────────────────────────────  
    FINAL SELF-CHECK (before returning)  
    ────────────────────────────────────────────────────  
    1. Does each field strictly respect character limits?  
    2. Is the message appropriate for the notification type?  
    3. Does the title immediately capture attention with relevance?  
    4. Does the text expand value proposition without redundancy?  
    5. Is the CTA actionable and creates appropriate urgency?  
    6. Is the tone luxury yet accessible for mobile context?  
    7. Are there no trigger words that cause spam filtering?  
    8. Correct and uniform language ({{language}})?  
    9. Does the messaging support overall omnichannel strategy?  

    If a point fails, **regenerate** the affected element before delivering.
    -->
    """

    system_template = SystemMessagePromptTemplate.from_template(system_prompt)

    # ------------- FEW-SHOT -------------

    few_shot_template = create_few_shot_prompt_template(
        example_module_path=f"models.{task.content_type.value.lower()}.examples.{data_input.type.value.lower()}",
        input_cls=OmniMessage,
        output_cls=out_cls
    )

    # ------------- CONTEXT -------------
    context_template = create_context_prompt_template(model, task, uploaded_files)

    # ------------- USER -------------
    user_template = HumanMessagePromptTemplate.from_template([
        f"Generate the output adhering EXACTLY to the following schema (do not add text, comments or superfluous spaces outside the block):\n{{format_instructions}}\n\n"
        f"IMPORTANT: Respond ONLY with the required structure, without explanations, additional text or trailing comma.\n\n"
        f"IMPORTANT: Respect character limits for each field.\n\n"
        f"IMPORTANT: Respond in {{language}}\n\n"
        f"INPUT TO ANALYZE: ```json\n{{input_json}}\n```"
    ])

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

    # ------------- CHAT PROMPT ---------
    templates = []

    templates.append(system_template)

    if few_shot_template:
        templates.append(few_shot_template)

    if context_template:
        templates.append(context_template)

    templates.append(user_template)

    chat_prompt = ChatPromptTemplate.from_messages(templates)

    # ------------- PARSER -------------

    parser = OutputFixingParser.from_llm(
        parser=PydanticOutputParser(pydantic_object=out_cls),
        llm=MODELS.get(os.getenv("AI_FIX_PARSING_MODEL"), model),
        max_retries=int(os.getenv("AI_FIX_PARSING_MAX_RETRIES", 2)),
    )

    # ------------- PIPELINE -------------
    chain = chat_prompt | model | parser

    prompt_inputs = {
        'input_json': data_input.model_dump_json(),
        'format_instructions': parser.get_format_instructions(),
        'language': task.language.complete_name,
        'task_type': data_input.type.value,
        "specific_prompt": specific_prompts.get(data_input.type),
        "custom_prompt": custom_prompt,
    }

    return chain, prompt_inputs, uploaded_files


def validate(task: GenerationTask, generation_result):
    return OmniMessageOut.model_validate(task.data | generation_result.model_dump())
