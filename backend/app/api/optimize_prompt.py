"""
Endpoint for optimizing user prompts/briefs for better AI generation.
Helps users who don't know prompt engineering to get better results.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging
import json

from app.core.config import settings
from app.core.vertex_ai import vertex_client

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class OptimizePromptRequest(BaseModel):
    """Request to optimize a user's brief/description"""
    text: str = Field(..., description="User's original brief or description")
    content_type: str = Field(default="newsletter", description="Type of content to generate")
    tone: str = Field(default="professional", description="Desired tone")
    structure: list[dict] = Field(..., description="Email structure (what components to generate)")


class OptimizePromptResponse(BaseModel):
    """Optimized prompt ready for AI generation"""
    optimized_prompt: str = Field(..., description="The optimized, detailed prompt")
    improvements: list[str] = Field(..., description="List of improvements made")


@router.post("/optimize-prompt", response_model=OptimizePromptResponse)
@limiter.limit(f"{settings.rate_limit_per_second}/second")
async def optimize_prompt(
    request: Request,
    req: OptimizePromptRequest,
) -> OptimizePromptResponse:
    """
    Transform a simple user description into an optimized prompt for AI generation.
    
    This helps users who aren't familiar with prompt engineering to get better results
    from the AI by adding context, structure, and clarity to their brief.
    """
    try:
        # Calculate max length based on whether structure includes images
        # Images use ~1000 tokens, so we need shorter prompts when images are present
        has_image_context = any('image' in str(s).lower() for s in req.structure)
        max_chars = 600 if has_image_context else 1000
        
        # Build the meta-prompt that will optimize the user's brief
        optimization_prompt = f"""You are an expert prompt engineer specializing in marketing content generation.

Your task is to transform a user's simple description into a detailed, effective prompt for generating email marketing content.

**User's Original Brief:**
{req.text}

**Context:**
- Content Type: {req.content_type}
- Tone: {req.tone}
- Structure: {', '.join([f"{s['component']} ({s['count']})" for s in req.structure])}

**Your Task:**
Transform this brief into an optimized prompt that will help an AI generate excellent email content. The optimized prompt should:

1. **Add Context**: Include target audience, brand positioning, and campaign goals if not specified
2. **Add Specificity**: Make vague descriptions more concrete with examples
3. **Add Structure**: Clearly explain what each component should achieve
4. **Add Style Guidelines**: Specify tone, length, and formatting expectations
5. **Add Key Messages**: Highlight what to emphasize and what to avoid

**Critical Constraints:**
- The optimized prompt MUST be under {max_chars} characters (current: {len(req.text)} chars)
- Be concise but informative - every word should add value
- Prioritize the most important details
- If the original brief is already long, consolidate and clarify rather than expand

**Important:**
- Keep the user's core intent and key information
- Add helpful details they might have missed
- Make it clear and actionable for content generation
- Don't invent product names or specific details - use placeholders if needed
- Focus on making the AI understand WHAT to create and HOW to write it
- STAY UNDER {max_chars} CHARACTERS - this is critical for AI stability

Return your response as JSON with this structure:
{{
    "optimized_prompt": "The complete, detailed prompt ready for AI generation (UNDER {max_chars} chars)",
    "improvements": ["Improvement 1: What you added/clarified", "Improvement 2: ...", "Improvement 3: ..."]
}}

Return ONLY the JSON, no other text."""

        # Call Vertex AI to optimize the prompt
        # Use direct generation without the "fixing" logic since we have custom JSON structure
        from vertexai.generative_models import GenerativeModel, GenerationConfig
        
        model = GenerativeModel(
            model_name="gemini-2.0-flash-001",
            generation_config=GenerationConfig(
                temperature=0.7,
                max_output_tokens=1500,
                response_mime_type="application/json"
            )
        )
        
        response = await model.generate_content_async(optimization_prompt)
        response_text = response.text
        
        # Parse response
        response_data = json.loads(response_text)
        optimized = response_data.get("optimized_prompt", req.text)
        improvements = response_data.get("improvements", [])
        
        # Validate length and force truncate if needed (shouldn't happen, but safety check)
        if len(optimized) > max_chars:
            logger.warning(f"Optimized prompt exceeded {max_chars} chars ({len(optimized)}), truncating...")
            # Truncate at sentence boundary
            truncated = optimized[:max_chars]
            last_period = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
            if last_period > max_chars * 0.8:  # Only truncate at sentence if it's not too far back
                optimized = optimized[:last_period + 1]
            else:
                optimized = truncated.rstrip() + "..."
            improvements.append(f"⚠️ Truncated to {len(optimized)} chars for AI stability")
        
        logger.info(f"Optimized prompt: {len(req.text)} chars → {len(optimized)} chars (limit: {max_chars})")
        
        return OptimizePromptResponse(
            optimized_prompt=optimized,
            improvements=improvements
        )

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse optimization response: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to parse AI response. Please try again."
        )
    except Exception as e:
        logger.error(f"Error optimizing prompt: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to optimize prompt: {str(e)}"
        )

