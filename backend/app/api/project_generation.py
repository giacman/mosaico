"""
Project-based Generation and Translation Endpoints
Combines AI generation with database persistence
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.vertex_ai import VertexAIClient, get_client
from app.db.session import get_db
from app.db.models import Project, Component, Translation, Image
from app.models.project_schemas import (
    GenerateProjectContentRequest,
    GenerateProjectContentResponse,
    TranslateProjectRequest,
    TranslateProjectResponse,
    ComponentResponse
)
from app.services.project_service import ProjectService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/projects/{project_id}/generate", response_model=GenerateProjectContentResponse)
async def generate_project_content(
    project_id: int,
    request: GenerateProjectContentRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_client: VertexAIClient = Depends(get_client)
):
    """
    Generate AI content for all components in a project
    
    - Uses project's brief, structure, and tone
    - Generates content for each component type (subject, body, cta, etc.)
    - Optionally uses uploaded images as context
    - Saves all generated content to database
    """
    
    # Get project with all relationships
    project = ProjectService.get_project(db, project_id, user_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Build the generation prompt
    prompt = f"{project.brief_text or 'Create email content'}"
    
    # Prepare structure for generation
    structure = []
    for item in project.structure:
        structure.append({
            "component": item["component"],
            "count": item["count"]
        })
    
    # Determine image URL (use first uploaded image if available, or from request)
    image_url = None
    if project.images:
        image_url = project.images[0].gcs_public_url
    elif request.image_urls:
        image_url = request.image_urls[0]
    
    try:
        # Call the AI generation endpoint
        from app.api.generate import build_generation_prompt
        
        ai_prompt = build_generation_prompt(
            text=prompt,
            count=request.count,
            tone=project.tone or "professional",
            content_type="newsletter",
            structure=structure,
            context=None
        )
        
        # Generate content
        response_text = await ai_client.generate_with_fixing(
            prompt=ai_prompt,
            expected_variations=request.count,
            temperature=0.7,
            max_tokens=2048,
            image_url=image_url
        )
        
        import json
        variations = json.loads(response_text).get("variations", [])
        
        if not variations:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No content generated"
            )
        
        # Take the first variation (for MVP, always generate 1)
        generated_content = variations[0]
        
        # Save each component to database
        components = []
        for key, value in generated_content.items():
            # Parse component type and index (e.g., "body_1" -> type="body", index=1)
            if "_" in key:
                parts = key.rsplit("_", 1)
                component_type = parts[0]
                component_index = int(parts[1])
            else:
                component_type = key
                component_index = None
            
            # Create component in database
            component = Component(
                project_id=project_id,
                component_type=component_type,
                component_index=component_index,
                generated_content=value
            )
            db.add(component)
            components.append(component)
        
        db.commit()
        
        # Refresh to get IDs
        for comp in components:
            db.refresh(comp)
        
        logger.info(f"Generated and saved {len(components)} components for project {project_id}")
        
        return GenerateProjectContentResponse(
            project_id=project_id,
            components=[ComponentResponse.from_orm(c) for c in components]
        )
        
    except Exception as e:
        logger.error(f"Error generating project content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content: {str(e)}"
        )


@router.post("/projects/{project_id}/translate", response_model=TranslateProjectResponse)
async def translate_project_content(
    project_id: int,
    request: TranslateProjectRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_client: VertexAIClient = Depends(get_client)
):
    """
    Translate all components in a project to target languages
    
    - Uses project's target languages if not specified in request
    - Translates each component's generated content
    - Saves all translations to database
    """
    
    # Get project
    project = ProjectService.get_project(db, project_id, user_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Determine target languages
    target_languages = request.languages or project.target_languages
    if not target_languages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No target languages specified"
        )
    
    # Get all components for this project
    components = db.query(Component).filter(
        Component.project_id == project_id
    ).all()
    
    if not components:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No components to translate. Generate content first."
        )
    
    try:
        # Translate each component for each language
        for component in components:
            if not component.generated_content:
                continue
            
            for lang_code in target_languages:
                # Call translation API
                from app.api.translate import translate_text_content
                
                translated_text = await translate_text_content(
                    text=component.generated_content,
                    target_language=lang_code.upper(),
                    source_language="EN",
                    ai_client=ai_client
                )
                
                # Save translation
                ProjectService.add_translation(
                    db=db,
                    component_id=component.id,
                    user_id=user_id,
                    language_code=lang_code,
                    translated_content=translated_text
                )
        
        # Refresh components to get translations
        db.refresh(project)
        updated_components = db.query(Component).filter(
            Component.project_id == project_id
        ).all()
        
        logger.info(f"Translated {len(components)} components for project {project_id}")
        
        return TranslateProjectResponse(
            project_id=project_id,
            components=[ComponentResponse.from_orm(c) for c in updated_components]
        )
        
    except Exception as e:
        logger.error(f"Error translating project content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to translate content: {str(e)}"
        )

