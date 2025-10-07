import os

from langchain.output_parsers import OutputFixingParser
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate

from models.editorial.classes import LLMEditorialOut, Editorial, LLMEditorialIn, validate_editorial_output
from models.generation_prompt import create_context_prompt_template, create_few_shot_prompt_template
from utils.LLMs import MODELS
from utils.task import GenerationTask


def generate(model, task: GenerationTask):
    uploaded_files = []

    data_input = LLMEditorialIn.model_validate(task.data)

    out_cls = LLMEditorialOut

    # -------------  SYSTEM  -------------
    system_prompt = f"""
    YOU WILL RECEIVE: a JSON file that outlines the article (fields title, excerpt, paragraphs, etc.), including for each paragraph and sub-paragraph:
    • **content_description**: brief indication of themes, tones or focus to develop.
    • **mention_list**: array of brands, products or specific references to integrate.

    OBJECTIVE: analyze the JSON and generate long, flowing texts rich in visuals and insights. **Do not summarize**: write a real article that meets the minimum sentence and word requirements indicated below.

    ────────────────────────────────────────────────────  
    TEXTS TO GENERATE  
    ────────────────────────────────────────────────────  
    ● **introduction**  
      - 1 or 2 paragraphs for a total **≥ 300 words**.  
      - Open with **a visual scene or rhetorical question** that directly engages the reader.  
      - Insert context (event, season, trend) and the **benefit** of the guide.  
      - Evoke key themes, colors, materials or looks.  
      - Close with **soft micro-CTA** (e.g., "Discover the complete selection", "Let yourself be inspired").  

    ● **paragraphs[].text**  
      - Minimum **150 words** (if NO subparagraphs: **≥ 300 words**).  
      - Frame the section: broad perspective → subsections.  
      - Use **second person** and fluid transitions.  
      - Insert the **primary keyword** within the first 100 words.  
      - **Use content_description**: if present, translate it into a guiding idea to enrich with narrative and contextual details.  
      - **Integrate mention_list**: cite each brand/product mentioned in this array organically, with descriptive anchors and within the textual flow.  

    ● **paragraphs[].subparagraphs[].text**  
      - **≥ 250 words**.  
      - If *product_description* is present, transform it into **sensory storytelling** (materials, fit, usage occasions, sustainable plus points).  
      - Links to runway, street-style or pop icons if relevant.  
      - **Respect content_description**: develop the suggested themes or mood, expanding their practical or emotional implications.  
      - **Insert mention_list**: if the array contains products or brands to cite, describe them in a real usage context, emphasizing the indicated plus points.  

    ● **paragraphs[].subparagraphs[].style_suggestions**  *(optional)*  
      - Bullet list (max 3) **only if the title implies practical advice**.  
      - Each bullet: max 100 words, initial capital, no final period.  
      - After the list, add **3–4 sentences** of stylistic suggestions.  

    ────────────────────────────────────────────────────  
    GENERAL GUIDELINES  
    ────────────────────────────────────────────────────  
    • **Voice**: second person, aspirational-consultative tone; alternate sensory adjectives ("velvety", "luminous") with precise technical terminology.  
    • **Rhythm**: mix of short and medium sentences; compact paragraphs, NO mechanical repetitions.  
    • **Bullet lists**: never two consecutive lists without connecting text.  
    • **SEO**: natural density; descriptive anchors; NO keyword stuffing.  
    • **Consistency**: pronouns, verb tenses and tone homogeneous; cohesion with title and excerpt.  
    • **CTA**: always soft, inspiration-oriented, not sales imperative.  
    • **Sustainability & values**: when relevant, integrate eco materials, craftsmanship, upcycling in narrative key.  
    • **Language**: {{language}}.  

    {{custom_prompt}}
    
    <!--
    WORKFLOW & SELF-CHECK  
    (Chain-of-Thought internal)

    ────────────────────────────────────────
    MENTAL WORKFLOW (step-by-step)
    ────────────────────────────────────────
    1. Read the JSON: note title, category, excerpt, keywords, empty fields.  
    2. Build a hierarchical outline:  
       • Introduction → paragraphs → subparagraphs → style_suggestions.  
    3. Match primary and secondary keywords to sections; plan ≤ 2 relevant internal links per paragraph.  
    4. If *product_description* is present, transform them into sensory storytelling (materials, fit, usage occasions, sustainable plus points).  
    5. Establish where a bullet list is needed and insert connecting text before/after.  
    6. Write texts following: second person voice, aspirational-consultative tone, minimum lengths.  
    7. Integrate soft final CTA in introduction and, if appropriate, at the end of the article.  
    8. Verify cohesion with title & excerpt; maintain language = {{language}}.  

    ────────────────────────────────────────
    FINAL SELF-CHECK (before returning)
    ────────────────────────────────────────
    1. Does each section meet the minimum word **and** sentence requirements?  
    2. Does the primary keyword appear within the first 100 words of each paragraph?  
    3. Does each paragraph contain **≤ 2 internal links** with descriptive anchors?  
    4. Bullet lists present only where expected, max 3 bullets, no consecutive lists without connecting text.  
    5. Soft CTA present, inspirational tone (no sales imperatives).  
    6. Language of entire output corresponds to {{language}}.
    7. Is the response compliant with the output structure? 

    If a point fails, **regenerate the affected section** before delivering the article.
    -->
    """
    system_template = SystemMessagePromptTemplate.from_template(system_prompt)

    # -------------  FEW-SHOT -------------
    few_shot_template = create_few_shot_prompt_template(
        example_module_path=f"models.{task.content_type.value.lower()}.examples",
        input_cls=Editorial,
        output_cls=out_cls
    )

    # -------------  CONTEXT  ----------------
    context_template = create_context_prompt_template(model, task, uploaded_files)

    # -------------  USER  ----------------
    user_template = HumanMessagePromptTemplate.from_template(
        [
            f"Generate the output adhering EXACTLY to the following schema (do not add text, comments or superfluous spaces outside the block):\n{{format_instructions}}\n\n"
            f"IMPORTANT: Respond ONLY with the required structure, without explanations, additional text or trailing comma.\n\n"
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

    prompt_inputs = {
        "input_json": data_input.model_dump_json(),
        "format_instructions": parser.get_format_instructions(),
        "language": task.language.complete_name,
        "custom_prompt": custom_prompt,
    }

    return chain, prompt_inputs, uploaded_files


def validate(task: GenerationTask, generation_result: LLMEditorialOut):
    return validate_editorial_output(Editorial.model_validate(task.data), generation_result)
