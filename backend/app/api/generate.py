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
    context: str | None = None
) -> str:
    """Builds the dynamic prompt for the generative model based on a requested structure."""
    
    structure_details = []
    json_example_structure = []
    
    for item in structure:
        plural = "s" if item.count > 1 else ""
        structure_details.append(f"{item.count} {item.component.value.replace('_', ' ')}{plural}")
        
        if item.count > 1:
            for i in range(1, item.count + 1):
                json_example_structure.append(f'    "{item.component.value}_{i}": "..."')
        else:
            json_example_structure.append(f'    "{item.component.value}": "..."')
            
    structure_list_str = ", ".join(structure_details)
    json_example_str = ",\n".join(json_example_structure)
    
    context_block = f"\nADDITIONAL CONTEXT:\n{context}\n" if context else ""

    prompt = f"""You are a senior copywriter and expert in content architecture, specialized in creating {content_type}.
Your task is to generate {count} variations of a structured content block based on the user's instruction.
Each variation must contain exactly the following components: {structure_list_str}.
Maintain a {tone} tone and brand voice consistency.
{context_block}
INSTRUCTION:
"{text}"

GUIDELINES:
- Generate creative and relevant text that aligns with the instruction for each component.
- For any component with a count greater than one (e.g., 2 CTAs), you MUST generate unique keys for each instance (e.g., "cta_1", "cta_2").
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
    request: GenerateVariationsRequest, client: VertexAIClient = Depends(get_client)
) -> GenerateVariationsResponse:
    """
    Generate variations of a text based on a prompt.
    """
    logger.info(
        f"Generating {request.count} variations | Tone: {request.tone.value} | "
        f"Type: {request.content_type.value} | Structure: {request.structure}"
    )

    prompt = build_generation_prompt(
        text=request.text,
        count=request.count,
        tone=request.tone.value,
        content_type=request.content_type.value,
        structure=request.structure,
        context=request.context,
    )

    raw_variations = await client.generate_with_fixing(
        prompt,
        request.count,
        temperature=0.7,
        max_tokens=2048,
        image_url=request.image_url,
    )

    try:
        variations_list = json.loads(raw_variations)
        
        logger.info(f"Successfully generated {len(variations_list)} variations")
        
        return GenerateVariationsResponse(
            variations=variations_list,
            original_text=request.text,
            tone=request.tone.value
        )
        
    except Exception as e:
        logger.error(f"Error in generate_variations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
