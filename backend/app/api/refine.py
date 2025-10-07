"""
Refine Endpoint
One-click text improvements: shorten, fix grammar, improve clarity, etc.
"""
from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging
import json

from app.models.schemas import RefineRequest, RefineResponse
from app.core.vertex_ai import vertex_client
from app.core.config import settings

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


OPERATION_PROMPTS = {
    "shorten": "Make this text more concise and impactful while preserving the core message. Remove unnecessary words.",
    "fix_grammar": "Fix any grammatical errors, spelling mistakes, and improve sentence structure. Maintain the original tone and meaning.",
    "improve_clarity": "Improve clarity and readability. Make the message clearer and easier to understand.",
    "make_formal": "Rewrite this text in a more formal, professional tone suitable for business communication.",
    "make_casual": "Rewrite this text in a more casual, friendly tone while maintaining professionalism."
}


def build_refine_prompt(text: str, operation: str, content_type: str) -> str:
    """Build prompt for text refinement"""
    
    operation_instruction = OPERATION_PROMPTS.get(operation, operation)
    
    prompt = f"""You are a professional copywriter specialized in {content_type} content.

Task: {operation_instruction}

Original text:
"{text}"

Output as JSON matching this structure:
{{
  "refined_text": "improved version here"
}}

Return ONLY the JSON object, no explanations, no markdown."""
    
    return prompt


@router.post("/refine", response_model=RefineResponse)
@limiter.limit(f"{settings.rate_limit_per_second}/second")
async def refine_text(
    request: Request,
    req: RefineRequest
) -> RefineResponse:
    """
    Refine text with one-click operations
    
    Operations:
    - shorten: Make text more concise
    - fix_grammar: Fix grammatical errors
    - improve_clarity: Improve readability
    - make_formal: Increase formality
    - make_casual: Decrease formality
    """
    try:
        logger.info(f"Refining with operation: {req.operation} | Type: {req.content_type}")
        
        prompt = build_refine_prompt(
            text=req.text,
            operation=req.operation,
            content_type=req.content_type.value
        )
        
        response_text = await vertex_client.generate_with_fixing(
            prompt=prompt,
            schema={"refined_text": "string"},
            temperature=0.5  # Balanced
        )
        
        response_data = json.loads(response_text)
        
        return RefineResponse(
            refined_text=response_data["refined_text"],
            original_text=req.text,
            operation=req.operation
        )
    
    except Exception as e:
        logger.error(f"Error in refine_text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
