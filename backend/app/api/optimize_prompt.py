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
    from the AI by adding context and clarity to their brief.
    """
    try:
        max_chars = 500  # Keep briefs concise for better AI performance
        
        # Build the meta-prompt that will optimize the user's brief
        optimization_prompt = f"""You are an expert prompt engineer specializing in marketing content.

Your task is to transform a user's simple description into a detailed, effective brief for generating marketing content.

**User's Original Brief:**
{req.text}

**Your Task:**
Transform this brief into an optimized version that will help an AI generate excellent content. The optimized brief should:

1. **Add Context**: Include target audience, brand positioning, and campaign goals if not specified
2. **Add Specificity**: Make vague descriptions more concrete
3. **Add Style Guidelines**: Specify tone and formatting expectations
4. **Add Key Messages**: Highlight what to emphasize and what to avoid

**Critical Constraints:**
- The optimized brief MUST be UNDER {max_chars} characters - this is CRITICAL
- Be very concise - every word must add value
- Prioritize the most important information
- If the original brief is already good, just polish it slightly

**Important:**
- Keep the user's core intent and key information
- Add helpful details they might have missed
- NEVER invent product names, prices, or specific details not provided
- NEVER use placeholders like [Product Name] or [Brand]
- Focus on brand values, emotions, and experiences

Return your response as JSON:
{{
    "optimized_prompt": "The improved brief (UNDER {max_chars} chars)",
    "improvements": ["What you improved 1", "What you improved 2", "What you improved 3"]
}}

Return ONLY valid JSON, no other text."""

        # Call Vertex AI to optimize the prompt
        from vertexai.generative_models import GenerativeModel, GenerationConfig
        
        model = GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=GenerationConfig(
                temperature=0.7,
                max_output_tokens=2048,
                response_mime_type="application/json"
            )
        )
        
        response = await model.generate_content_async(optimization_prompt)
        response_text = response.text
        
        logger.debug(f"Raw AI response: {response_text[:500]}...")
        
        # Parse response with fallback
        try:
            response_data = json.loads(response_text)
        except json.JSONDecodeError as parse_error:
            logger.error(f"JSON parse error: {parse_error}")
            logger.error(f"Raw response (first 1000 chars): {response_text[:1000]}")
            
            # Try to extract content manually as fallback
            import re
            
            # Try complete string first
            match = re.search(r'"optimized_prompt"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', response_text)
            if match:
                logger.info("Recovered optimized_prompt using regex fallback")
                return OptimizePromptResponse(
                    optimized_prompt=match.group(1).replace('\\"', '"').replace('\\n', '\n'),
                    improvements=["⚠️ Recovered from partial AI response"]
                )
            
            # If truncated, try to extract whatever we have
            match = re.search(r'"optimized_prompt"\s*:\s*"([^"]+)', response_text)
            if match:
                truncated_text = match.group(1).replace('\\"', '"').replace('\\n', '\n')
                # Find last complete sentence
                last_period = max(truncated_text.rfind('.'), truncated_text.rfind('!'), truncated_text.rfind('?'))
                if last_period > len(truncated_text) * 0.5:
                    truncated_text = truncated_text[:last_period + 1]
                else:
                    truncated_text = truncated_text.rstrip() + "..."
                logger.info(f"Recovered truncated optimized_prompt: {len(truncated_text)} chars")
                return OptimizePromptResponse(
                    optimized_prompt=truncated_text,
                    improvements=["⚠️ Response was truncated, recovered partial content"]
                )
            raise
            
        optimized = response_data.get("optimized_prompt", req.text)
        improvements = response_data.get("improvements", [])
        
        # Validate length and truncate if needed
        if len(optimized) > max_chars:
            logger.warning(f"Optimized prompt exceeded {max_chars} chars ({len(optimized)}), truncating...")
            truncated = optimized[:max_chars]
            last_period = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
            if last_period > max_chars * 0.8:
                optimized = optimized[:last_period + 1]
            else:
                optimized = truncated.rstrip() + "..."
            improvements.append(f"⚠️ Truncated to {len(optimized)} chars")
        
        logger.info(f"Optimized prompt: {len(req.text)} chars → {len(optimized)} chars")
        
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
