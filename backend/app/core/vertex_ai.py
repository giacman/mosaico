"""
Vertex AI Client Setup
Modern approach - NO LangChain, direct Vertex AI SDK
"""
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from app.core.config import settings
import logging
import os
import json

logger = logging.getLogger(__name__)


class VertexAIClient:
    """Wrapper for Vertex AI client with rate limiting and error handling"""
    
    def __init__(self):
        """Initialize Vertex AI client"""
        
        # Check for explicit credentials (Service Account for local dev)
        creds_path = settings.google_application_credentials
        
        if creds_path and os.path.exists(creds_path):
            # Use explicit Service Account credentials (local dev)
            logger.info(f"Using Service Account credentials from: {creds_path}")
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
        else:
            # Use Application Default Credentials (Cloud Run or ADC)
            logger.info("Using Application Default Credentials (ADC)")
        
        # Initialize Vertex AI
        vertexai.init(
            project=settings.gcp_project_id,
            location=settings.gcp_location
        )
        
        logger.info(f"Vertex AI initialized for project: {settings.gcp_project_id}")
    
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
            # Create model instance
            generative_model = GenerativeModel(model_name)
            
            # Configure generation
            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                response_mime_type=response_mime_type
            )
            
            # Generate content
            response = generative_model.generate_content(
                prompt,
                generation_config=generation_config
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
        current_prompt = prompt
        
        for attempt in range(max_retries + 1):
            response_text = ""
            try:
                response_text = await self.generate_content(
                    prompt=current_prompt,
                    temperature=temperature,
                    response_mime_type="application/json"
                )
                
                # Validate JSON format
                json.loads(response_text)
                
                return response_text
            
            except (json.JSONDecodeError, Exception) as e:
                last_error = e
                
                if attempt < max_retries:
                    logger.warning(f"Attempt {attempt + 1} failed with error: {e}. Trying to fix...")
                    
                    fix_prompt = f"""The following JSON output is malformed or invalid:

{response_text if response_text else 'No output generated'}

Error: {str(e)}

Expected schema:
{json.dumps(schema)}

Please fix the JSON and return ONLY valid JSON matching the schema above.
Ensure all special characters within strings are properly escaped (e.g., newlines as \\n, quotes as \\").
NO markdown formatting, NO explanations, ONLY the JSON object."""
                    
                    current_prompt = fix_prompt
                else:
                    logger.error(f"All {max_retries + 1} attempts failed. Last error: {last_error}")
                    raise last_error
        
        raise last_error # Should not be reached


# Global client instance
vertex_client = VertexAIClient()
