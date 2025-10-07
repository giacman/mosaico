"""
Vertex AI Client Setup
Modern approach - NO LangChain, direct Vertex AI SDK
"""
from google import genai
from google.genai import types
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class VertexAIClient:
    """Wrapper for Vertex AI client with rate limiting and error handling"""
    
    def __init__(self):
        """Initialize Vertex AI client"""
        self.client = genai.Client(
            vertexai=True,
            project=settings.gcp_project_id,
            location=settings.gcp_location
        )
        logger.info(f"Vertex AI client initialized for project: {settings.gcp_project_id}")
    
    async def generate_content(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        response_mime_type: str = "application/json"
    ) -> str:
        """
        Generate content using Vertex AI
        
        Args:
            prompt: The prompt text
            model: Model name (defaults to settings.vertex_ai_model)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum output tokens
            response_mime_type: Output format (application/json or text/plain)
        
        Returns:
            Generated text content
        """
        model_name = model or settings.vertex_ai_model
        
        try:
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    response_mime_type=response_mime_type
                )
            )
            
            return response.text
        
        except Exception as e:
            logger.error(f"Error generating content with {model_name}: {str(e)}")
            raise
    
    async def generate_with_fixing(
        self,
        prompt: str,
        schema: dict,
        max_retries: int = 2,
        temperature: float = 0.7
    ) -> str:
        """
        Generate content with self-healing JSON parsing
        Pattern from InventioHub but without LangChain OutputFixingParser
        
        Args:
            prompt: The prompt with schema instructions
            schema: JSON schema dict for validation error messages
            max_retries: Maximum retry attempts
            temperature: Sampling temperature
        
        Returns:
            Valid JSON string
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                # First attempt or retry with fixing prompt
                response_text = await self.generate_content(
                    prompt=prompt,
                    temperature=temperature,
                    response_mime_type="application/json"
                )
                
                return response_text
            
            except Exception as e:
                last_error = e
                
                if attempt < max_retries:
                    # Use faster/cheaper model for fixing
                    logger.warning(f"Attempt {attempt + 1} failed, trying to fix...")
                    
                    fix_prompt = f"""The following JSON output is malformed or invalid:

{response_text if 'response_text' in locals() else 'No output generated'}

Error: {str(e)}

Expected schema:
{schema}

Please fix the JSON and return ONLY valid JSON matching the schema above.
NO markdown formatting, NO explanations, ONLY the JSON object."""
                    
                    prompt = fix_prompt
                else:
                    logger.error(f"All {max_retries + 1} attempts failed")
                    raise last_error


# Global client instance
vertex_client = VertexAIClient()
