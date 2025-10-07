"""
Generate Variations Endpoint
Core feature: Generate text variations with tone-of-voice consistency
Pattern from InventioHub but NO LangChain - Direct Vertex AI SDK
"""
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging
import json

from app.models.schemas import (
    GenerateVariationsRequest,
    GenerateVariationsResponse
)
from app.core.vertex_ai import vertex_client
from app.core.config import settings

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


# ==============================================================================
# FEW-SHOT EXAMPLES (Tone of Voice)
# In production, load from Cloud Storage
# ==============================================================================

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
        ]
    }
}


def load_few_shot_examples(content_type: str, tone: str) -> str:
    """
    Load few-shot examples for prompt
    Pattern from InventioHub few-shot learning
    
    TODO: Load from Cloud Storage in production
    """
    examples = FEW_SHOT_EXAMPLES.get(content_type, {}).get(tone, [])
    
    if not examples:
        # Fallback to professional if tone not found
        examples = FEW_SHOT_EXAMPLES.get(content_type, {}).get("professional", [])
    
    formatted_examples = []
    for i, ex in enumerate(examples, 1):
        formatted_examples.append(
            f"Example {i}:\n"
            f"Input: \"{ex['input']}\"\n"
            f"Output: {json.dumps(ex['output'], ensure_ascii=False)}"
        )
    
    return "\n\n".join(formatted_examples)


def build_generation_prompt(
    text: str,
    count: int,
    tone: str,
    content_type: str,
    context: str | None = None
) -> str:
    """
    Build prompt for variation generation
    Structure inspired by InventioHub prompt engineering
    """
    
    # Load few-shot examples
    examples = load_few_shot_examples(content_type, tone)
    
    # Context section (if provided)
    context_section = ""
    if context:
        context_section = f"""
CONTEXT:
{context}
"""
    
    # Main prompt (inspired by InventioHub structure)
    prompt = f"""You are a senior copywriter specialized in creating {content_type} content.

Your task is to generate {count} variations of the provided text, maintaining a {tone} tone and brand voice consistency.

GUIDELINES:
- Maintain the core message and intent
- Adapt length appropriately (variations can be shorter or slightly longer)
- Ensure each variation is distinct and creative
- Use clear, scannable language
- Maintain brand voice consistency with examples
- Output ONLY as valid JSON array

{examples}
{context_section}

NOW GENERATE {count} VARIATIONS:
Input: "{text}"

Output as JSON matching this exact structure:
{{
  "variations": ["variation 1", "variation 2", "variation 3"]
}}

Return ONLY the JSON object, no explanations, no markdown formatting."""
    
    return prompt


@router.post("/generate", response_model=GenerateVariationsResponse)
@limiter.limit(f"{settings.rate_limit_per_second}/second")
async def generate_variations(
    request: Request,
    req: GenerateVariationsRequest
) -> GenerateVariationsResponse:
    """
    Generate text variations with tone-of-voice consistency
    
    This endpoint generates multiple creative variations of input text,
    maintaining brand voice through few-shot learning (RAG pattern from InventioHub)
    """
    try:
        logger.info(f"Generating {req.count} variations | Tone: {req.tone} | Type: {req.content_type}")
        
        # Build prompt with few-shot examples
        prompt = build_generation_prompt(
            text=req.text,
            count=req.count,
            tone=req.tone.value,
            content_type=req.content_type.value,
            context=req.context
        )
        
        # Generate with Vertex AI (with self-healing)
        response_text = await vertex_client.generate_with_fixing(
            prompt=prompt,
            schema={"variations": ["string"]},
            temperature=0.8  # More creative for variations
        )
        
        # Parse response
        try:
            response_data = json.loads(response_text)
            variations = response_data.get("variations", [])
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {response_text}")
            raise HTTPException(status_code=500, detail="Invalid AI response format")
        
        # Validate we got the right number
        if len(variations) != req.count:
            logger.warning(f"Expected {req.count} variations, got {len(variations)}")
            # Pad or truncate if needed
            if len(variations) < req.count:
                variations.extend([req.text] * (req.count - len(variations)))
            else:
                variations = variations[:req.count]
        
        logger.info(f"Successfully generated {len(variations)} variations")
        
        return GenerateVariationsResponse(
            variations=variations,
            original_text=req.text,
            tone=req.tone.value
        )
    
    except Exception as e:
        logger.error(f"Error in generate_variations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
