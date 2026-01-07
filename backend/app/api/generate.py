"""
Generate Variations Endpoint
Core feature: Generate text variations with tone-of-voice consistency
Pattern from InventioHub but NO LangChain - Direct Vertex AI SDK
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging
import json
import asyncio

from app.models.schemas import (
    GenerateVariationsRequest,
    GenerateVariationsResponse,
    ContentType,
    ToneType,
    ComponentType,
    StructureComponent
)
from app.core.vertex_ai import VertexAIClient, get_client
from app.core.config import settings
from app.utils.notifications import notify_generation_completed
from app.prompts.few_shot_loader import get_few_shot_db

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)
router = APIRouter()

# --- Few-Shot Examples (Hardcoded for Simplicity) ---
# In production, this would load from a database or GCS
FEW_SHOT_EXAMPLES = {
    "newsletter": {
        "professional": [
            {
                "input": "Nuova collezione primavera",
                "output": [
                    "Scopri la nuova collezione primavera/estate",
                    "La collezione PE2025 ti aspetta",
                    "Novità stagionali: esplora la gamma"
                ]
            },
            {
                "input": "Saldi fino a 50%",
                "output": [
                    "Saldi esclusivi: fino a 50% di sconto",
                    "Risparmia fino alla metà su articoli selezionati",
                    "Offerta limitata: -50% su tutta la collezione"
                ]
            }
        ],
        "enthusiastic": [
            {
                "input": "Nuova collezione primavera",
                "output": [
                    "✨ Pronta a brillare? La collezione primavera ti aspetta!",
                    "È arrivata! Scopri ora la PE2025",
                    "Finalmente qui: la tua nuova ossessione fashion"
                ]
            }
        ],
        "cta": [
            {"input": "New user discount", "output": ["Shop Now & Save 15%", "Claim Your Discount", "Explore the Collection"]},
        ]
    }
}

COMPONENT_INSTRUCTIONS = {
    ComponentType.FULL_EMAIL: "a full newsletter email structure, including a subject, pre-header, two body sections, and two calls to action (CTAs)",
    ComponentType.SUBJECT: "a compelling subject line",
    ComponentType.PRE_HEADER: "a concise and engaging pre-header",
    ComponentType.BODY: "a detailed body section for a newsletter",
    ComponentType.CTA: "a clear and persuasive call to action (CTA)"
}

def load_few_shot_examples(content_type: ContentType, tone: ToneType, component: ComponentType) -> str:
    """
    Loads few-shot examples based on content type, tone, and component.
    For now, it's a simplified placeholder.
    """
    # Simplified logic: Use component-specific examples if they exist, otherwise fallback
    component_key = component.value if component != ComponentType.FULL_EMAIL else "subject" # Use subject as a proxy for email
    
    examples = FEW_SHOT_EXAMPLES.get(component_key.lower(), {}).get(tone.value.lower(), [])
    if not examples:
        return ""
    
    formatted_examples = "\n".join([
        f"- Input: {ex['input']}\n  Output: {json.dumps(ex['output'])}"
        for ex in examples
    ])
    return f"Here are some examples of the desired output format and style:\n{formatted_examples}\n"


def build_generation_prompt(
    text: str,
    count: int,
    tone: str,
    content_type: str,
    structure: list[StructureComponent],
    context: str | None = None,
    use_few_shot: bool = False,
    has_image: bool = False
) -> str:
    """
    Builds the dynamic prompt for the generative model based on a requested structure.
    
    Args:
        text: User's instruction text
        count: Number of variations to generate
        tone: Tone of voice
        content_type: Type of content (newsletter, etc.)
        structure: List of components to generate
        context: Optional additional context
        use_few_shot: If True, include Few-Shot examples (recommended for regeneration only)
        has_image: If True, include instructions for analyzing the provided image
    
    Returns:
        Formatted prompt string
    """
    
    structure_details = []
    json_example_structure = []
    
    # Track which component types are in the structure for Few-Shot examples
    component_types_in_structure = set()
    
    for item in structure:
        plural = "s" if item.count > 1 else ""
        structure_details.append(f"{item.count} {item.component.value.replace('_', ' ')}{plural}")
        component_types_in_structure.add(item.component.value)
        
        if item.count > 1:
            for i in range(1, item.count + 1):
                json_example_structure.append(f'    "{item.component.value}_{i}": "..."')
        else:
            json_example_structure.append(f'    "{item.component.value}": "..."')
            
    structure_list_str = ", ".join(structure_details)
    json_example_str = ",\n".join(json_example_structure)
    
    context_block = f"\nADDITIONAL CONTEXT:\n{context}\n" if context else ""
    
    # Content type specific guidelines
    content_type_guidelines = ""
    if content_type == "push_notification":
        content_type_guidelines = """
=== PUSH NOTIFICATION SPECIFIC RULES ===
You are creating mobile push notifications. These must be:
- **TITLE**: Maximum 20 characters - punchy, attention-grabbing headline
- **BODY**: Maximum 100 characters - urgent, action-oriented message
- **CTA** (if included): Maximum 30 characters or 3 words - clear call to action
- **URGENT & ACTION-ORIENTED**: Create a sense of immediacy
- **DIRECT**: Get to the point immediately, no filler words
- **COMPELLING**: Make the user want to tap immediately
- **EMOJI-FRIENDLY**: Use 1-2 emojis strategically (optional but effective)

Examples of great push notifications:
✅ Title: "New arrivals 🔥" (13 chars) | Body: "Discover this season's must-haves before they're gone" (54 chars)
✅ Title: "Exclusive access" (16 chars) | Body: "Private sale starts now. Shop first." (37 chars)
✅ Title: "Don't miss out ⚡" (15 chars) | Body: "Limited pieces, unlimited style." (33 chars)

⚠️ CHARACTER LIMITS ARE STRICT - Count characters carefully!

"""
    
    # Visual context section - only included when an image is provided
    visual_context_section = ""
    if has_image:
        visual_context_section = """
=== VISUAL CONTEXT ===
An image has been provided along with this prompt. You MUST analyze it carefully and use it to inform your content:

1. **Identify key visual elements**: Products shown, setting, mood, colors, textures, and visual style
2. **Contextualize your copy**: Reference what you observe - the atmosphere, the aesthetic, the emotions evoked
3. **Complement the visual**: Your text should feel like it was written specifically FOR this image
4. **Be specific but not inventive**: Describe what you SEE (e.g., "elegant evening wear", "warm autumn tones") but do NOT invent product names you cannot verify

Your content should create a cohesive story with the image - the reader should feel the text and image belong together.

"""
    
    # Load Few-Shot examples ONLY if requested (for regeneration)
    # This keeps initial generation prompts lighter and more stable
    few_shot_section = ""
    if use_few_shot:
        few_shot_db = get_few_shot_db()
        few_shot_blocks = []
        
        for comp_type in component_types_in_structure:
            formatted_examples = few_shot_db.format_examples_for_prompt(
                component_type=comp_type,
                count=8  # Include 8 examples per component type
            )
            if formatted_examples:
                few_shot_blocks.append(formatted_examples)
        
        few_shot_section = "\n".join(few_shot_blocks) if few_shot_blocks else ""

    prompt = f"""You are a senior copywriter and expert in content architecture, specialized in creating {content_type}.
Your task is to generate {count} variations of a structured content block based on the user's instruction.
Each variation must contain exactly the following components: {structure_list_str}.
Maintain a {tone} tone and brand voice consistency.
{context_block}
INSTRUCTION:
"{text}"
{content_type_guidelines}{visual_context_section}
{few_shot_section}

=== CRITICAL CONTENT RULES ===
⛔ ABSOLUTELY FORBIDDEN:
1. DO NOT invent, fabricate, or mention specific product names (e.g., "Oversized Distressed Knitwear", "1996 Straight-Fit Jeans")
2. DO NOT use ANY placeholders with brackets like [Product Name], [Brand], [Insert here], etc.
3. DO NOT make up prices, discounts, or dates unless explicitly provided in the instruction
4. DO NOT reference specific collections, capsules, or collaborations unless mentioned in the instruction

✅ WHAT TO DO INSTEAD:
- Use general, evocative language: "new arrivals", "this season's pieces", "the collection", "our latest designs"
- Focus on emotions, experiences, and brand values rather than specific items
- Describe qualities: "luxurious materials", "timeless elegance", "impeccable craftsmanship"
- Write complete, polished text ready for immediate publication

EXAMPLE OF FORBIDDEN OUTPUT:
❌ "Discover the [Cashmere Blend Coat] and the [Heritage Loafers]..."
❌ "This season's arrivals feature the Oversized Cable Knit Sweater..."

EXAMPLE OF CORRECT OUTPUT:
✅ "Discover our latest arrivals, designed with timeless elegance in mind..."
✅ "This season's collection embodies refined craftsmanship and understated luxury..."

=== OUTPUT GUIDELINES ===
- IMPORTANT: You MUST always respond in ENGLISH. Even if the INSTRUCTION is in another language (e.g., Italian), your output MUST be in English.
- Generate creative and relevant text that aligns with the instruction for each component.
- For any component with a count greater than one (e.g., 2 CTAs), you MUST generate unique keys for each instance (e.g., "cta_1", "cta_2").
- Each instance MUST be completely DIFFERENT from the others - use different words, phrasing, and creative angles.
- The value for every key in the JSON object MUST be a single string.
- Output ONLY as a valid JSON object containing a single key "variations".
- The "variations" key must be a list of "flat" JSON objects, where each object is one complete content variation.

EXAMPLE OF THE EXACT JSON OUTPUT STRUCTURE REQUIRED:
{{
  "variations": [
    {{
{json_example_str}
    }},
    // ... more variations if count > 1 ...
  ]
}}
"""
    return prompt

@router.post("/generate", response_model=GenerateVariationsResponse, status_code=200)
@limiter.limit(f"{settings.rate_limit_per_second}/second")
async def generate_variations(
    request: Request,
    req: GenerateVariationsRequest,
    client: VertexAIClient = Depends(get_client)
) -> GenerateVariationsResponse:
    """
    Generate variations of a text based on a prompt.
    """
    logger.info(
        f"Generating {req.count} variations | Tone: {req.tone.value} | "
        f"Type: {req.content_type.value} | Structure: {req.structure}"
    )

    # Use Few-Shot examples only if requested (for regeneration)
    use_few_shot = req.use_few_shot if req.use_few_shot is not None else False
    
    # Check if an image is provided for visual context
    has_image = bool(req.image_url)
    
    prompt = build_generation_prompt(
        text=req.text,
        count=req.count,
        tone=req.tone.value,
        content_type=req.content_type.value,
        structure=req.structure,
        context=req.context,
        use_few_shot=use_few_shot,
        has_image=has_image,
    )

    # Use provided temperature or default to 0.7
    temperature = req.temperature if req.temperature is not None else 0.7
    
    # Use Flash model if requested (faster/cheaper for CTAs)
    use_flash = req.use_flash if req.use_flash is not None else False
    
    raw_variations = await client.generate_with_fixing(
        prompt,
        req.count,
        temperature=temperature,
        max_tokens=2048,
        image_url=req.image_url,
        use_flash=use_flash,
    )

    try:
        # Parse the JSON response
        response_data = json.loads(raw_variations)
        
        # Extract the variations array from the response
        variations_list = response_data.get("variations", [])
        
        logger.info(f"Successfully generated {len(variations_list)} variations")
        
        # Send Slack notification (non-blocking)
        component_count = sum(comp.count for comp in req.structure)
        asyncio.create_task(
            notify_generation_completed(
                project_name="Unknown",  # Will be enriched when we have project context
                component_count=component_count,
                user_email=None
            )
        )
        
        return GenerateVariationsResponse(
            variations=variations_list,
            original_text=req.text,
            tone=req.tone.value
        )
        
    except Exception as e:
        logger.error(f"Error in generate_variations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
