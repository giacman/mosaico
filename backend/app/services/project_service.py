"""
Service layer for Project operations
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.db.models import Project, Component, Translation, Image
from app.models.project_schemas import (
    ProjectCreate,
    ProjectUpdate,
    ComponentCreate,
    ComponentUpdate
)

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for managing projects"""
    
    @staticmethod
    def create_project(db: Session, user_id: str, project_data: ProjectCreate) -> Project:
        """Create a new project"""
        # Convert structure to dict format for JSON storage
        structure_dict = [item.model_dump() for item in project_data.structure]
        
        project = Project(
            user_id=user_id,
            name=project_data.name,
            brief_text=project_data.brief_text,
            structure=structure_dict,
            tone=project_data.tone,
            target_languages=project_data.target_languages or []
        )
        
        db.add(project)
        db.commit()
        db.refresh(project)
        
        logger.info(f"Created project {project.id} for user {user_id}")
        return project
    
    @staticmethod
    def get_project(db: Session, project_id: int, user_id: str) -> Optional[Project]:
        """Get a project by ID (with authorization check)"""
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == user_id
        ).options(
            joinedload(Project.components).joinedload(Component.translations),
            joinedload(Project.images)
        ).first()
        
        return project
    
    @staticmethod
    def list_projects(db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[Project]:
        """List all projects for a user"""
        projects = db.query(Project).filter(
            Project.user_id == user_id
        ).order_by(
            Project.updated_at.desc()
        ).offset(skip).limit(limit).all()
        
        return projects
    
    @staticmethod
    def update_project(
        db: Session,
        project_id: int,
        user_id: str,
        project_data: ProjectUpdate
    ) -> Optional[Project]:
        """Update a project"""
        project = ProjectService.get_project(db, project_id, user_id)
        
        if not project:
            return None
        
        update_data = project_data.model_dump(exclude_unset=True)
        
        # Handle structure conversion
        if "structure" in update_data and update_data["structure"]:
            update_data["structure"] = [item.model_dump() for item in project_data.structure]
        
        for field, value in update_data.items():
            setattr(project, field, value)
        
        db.commit()
        db.refresh(project)
        
        logger.info(f"Updated project {project_id}")
        return project
    
    @staticmethod
    def delete_project(db: Session, project_id: int, user_id: str) -> bool:
        """Delete a project"""
        project = ProjectService.get_project(db, project_id, user_id)
        
        if not project:
            return False
        
        db.delete(project)
        db.commit()
        
        logger.info(f"Deleted project {project_id}")
        return True
    
    @staticmethod
    def create_component(
        db: Session,
        project_id: int,
        user_id: str,
        component_data: ComponentCreate
    ) -> Optional[Component]:
        """Create a component for a project"""
        # Verify project ownership
        project = ProjectService.get_project(db, project_id, user_id)
        if not project:
            return None
        
        component = Component(
            project_id=project_id,
            component_type=component_data.component_type,
            component_index=component_data.component_index,
            generated_content=component_data.generated_content,
            component_url=component_data.component_url,
            image_id=component_data.image_id
        )
        
        db.add(component)
        db.commit()
        db.refresh(component)
        
        return component
    
    @staticmethod
    def update_component(
        db: Session,
        component_id: int,
        user_id: str,
        component_data: ComponentUpdate
    ) -> Optional[Component]:
        """Update a component"""
        component = db.query(Component).join(Project).filter(
            Component.id == component_id,
            Project.user_id == user_id
        ).first()
        
        if not component:
            return None
        
        update_data = component_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(component, field, value)
        
        db.commit()
        db.refresh(component)
        
        return component
    
    @staticmethod
    def add_translation(
        db: Session,
        component_id: int,
        user_id: str,
        language_code: str,
        translated_content: str
    ) -> Optional[Translation]:
        """Add a translation for a component"""
        # Verify ownership through component -> project
        component = db.query(Component).join(Project).filter(
            Component.id == component_id,
            Project.user_id == user_id
        ).first()
        
        if not component:
            return None
        
        # Check if translation already exists
        existing = db.query(Translation).filter(
            Translation.component_id == component_id,
            Translation.language_code == language_code
        ).first()
        
        if existing:
            # Update existing translation
            existing.translated_content = translated_content
            db.commit()
            db.refresh(existing)
            return existing
        
        # Create new translation
        translation = Translation(
            component_id=component_id,
            language_code=language_code,
            translated_content=translated_content
        )
        
        db.add(translation)
        db.commit()
        db.refresh(translation)
        
        return translation

