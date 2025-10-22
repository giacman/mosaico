"""
Service layer for Project operations
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.db.models import Project, Component, Translation, Image, ActivityLog
from app.models.project_schemas import (
    ProjectCreate,
    ProjectUpdate,
    ComponentCreate,
    ComponentUpdate
)

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for managing projects with collaboration support"""
    
    @staticmethod
    def _log_activity(
        db: Session,
        project_id: int,
        user_id: str,
        user_name: Optional[str],
        action: str,
        field_changed: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None
    ):
        """Log an activity for audit trail"""
        log_entry = ActivityLog(
            project_id=project_id,
            user_id=user_id,
            user_name=user_name,
            action=action,
            field_changed=field_changed,
            old_value=old_value,
            new_value=new_value
        )
        db.add(log_entry)
        # Don't commit here - let the main operation commit both together
    
    @staticmethod
    def create_project(
        db: Session,
        user_id: str,
        user_name: Optional[str],
        project_data: ProjectCreate
    ) -> Project:
        """Create a new project"""
        # Convert structure to dict format for JSON storage
        structure_dict = [item.model_dump() for item in project_data.structure]
        
        # Handle status value (enum or string)
        status_val = getattr(project_data.status, "value", None) or getattr(project_data, "status", None) or "in_progress"

        project = Project(
            name=project_data.name,
            brief_text=project_data.brief_text,
            structure=structure_dict,
            tone=project_data.tone,
            target_languages=project_data.target_languages or [],
            labels=project_data.labels or [],
            status=status_val,
            created_by_user_id=user_id,
            created_by_user_name=user_name
        )
        
        db.add(project)
        db.flush()  # Get ID before logging
        
        # Log creation
        ProjectService._log_activity(
            db, project.id, user_id, user_name, "created_project"
        )
        
        db.commit()
        db.refresh(project)
        
        logger.info(f"Created project {project.id} by user {user_id}")
        return project
    
    @staticmethod
    def duplicate_project(
        db: Session,
        project_id: int,
        user_id: str,
        user_name: Optional[str]
    ) -> Project:
        """Duplicate an existing project with all its components, translations, and images"""
        # Get original project with all relationships
        original = db.query(Project).options(
            joinedload(Project.components).joinedload(Component.translations),
            joinedload(Project.images)
        ).filter(Project.id == project_id).first()
        
        if not original:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        # Create new project with "(Copy)" suffix
        new_project = Project(
            name=f"{original.name} (Copy)",
            brief_text=original.brief_text,
            structure=original.structure,
            tone=original.tone,
            target_languages=original.target_languages,
            created_by_user_id=user_id,
            created_by_user_name=user_name
        )
        
        db.add(new_project)
        db.flush()  # Get new project ID
        
        # Duplicate components and their translations
        for orig_component in original.components:
            new_component = Component(
                project_id=new_project.id,
                component_type=orig_component.component_type,
                component_index=orig_component.component_index,
                generated_content=orig_component.generated_content,
                component_url=orig_component.component_url,
                image_id=orig_component.image_id
            )
            db.add(new_component)
            db.flush()  # Get new component ID
            
            # Duplicate translations
            for orig_translation in orig_component.translations:
                new_translation = Translation(
                    component_id=new_component.id,
                    language_code=orig_translation.language_code,
                    translated_content=orig_translation.translated_content
                )
                db.add(new_translation)
        
        # Duplicate images (they reference the same GCS files)
        for orig_image in original.images:
            new_image = Image(
                project_id=new_project.id,
                user_id=user_id,  # Use current user as uploader of duplicated images
                filename=orig_image.filename,
                gcs_path=orig_image.gcs_path,
                gcs_public_url=orig_image.gcs_public_url
            )
            db.add(new_image)
        
        # Log duplication
        ProjectService._log_activity(
            db, new_project.id, user_id, user_name, 
            "duplicated_project", 
            field_changed="source_project_id",
            new_value=str(project_id)
        )
        
        db.commit()
        db.refresh(new_project)
        
        logger.info(f"Duplicated project {project_id} to new project {new_project.id} by user {user_id}")
        return new_project
    
    @staticmethod
    def get_project(db: Session, project_id: int) -> Optional[Project]:
        """
        Get a project by ID
        NOTE: No user_id filtering - all users can see all projects
        """
        project = db.query(Project).filter(
            Project.id == project_id
        ).options(
            joinedload(Project.components).joinedload(Component.translations),
            joinedload(Project.images),
            joinedload(Project.activity_logs)
        ).first()
        
        return project
    
    @staticmethod
    def list_projects(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
        """
        List all projects (shared across all users)
        """
        projects = db.query(Project).order_by(
            Project.updated_at.desc()
        ).offset(skip).limit(limit).all()
        
        return projects
    
    @staticmethod
    def update_project(
        db: Session,
        project_id: int,
        user_id: str,
        user_name: Optional[str],
        project_data: ProjectUpdate
    ) -> Optional[Project]:
        """Update a project"""
        project = ProjectService.get_project(db, project_id)
        
        if not project:
            return None
        
        update_data = project_data.model_dump(exclude_unset=True)

        # Normalize status if present (accept enum or string)
        if "status" in update_data and update_data["status"] is not None:
            status_val = getattr(project_data.status, "value", None) or update_data["status"]
            update_data["status"] = status_val
        
        # Track changes for activity log
        changes = []
        
        # Handle structure conversion
        if "structure" in update_data and update_data["structure"]:
            update_data["structure"] = [item.model_dump() for item in project_data.structure]
        
        for field, value in update_data.items():
            if hasattr(project, field):
                old_value = getattr(project, field)
                if old_value != value:
                    changes.append((field, str(old_value), str(value)))
                setattr(project, field, value)
        
        # Update audit fields
        project.updated_by_user_id = user_id
        project.updated_by_user_name = user_name
        
        # Log each changed field
        for field, old_val, new_val in changes:
            ProjectService._log_activity(
                db, project_id, user_id, user_name,
                f"updated_{field}", field, old_val, new_val
            )
        
        db.commit()
        db.refresh(project)
        
        logger.info(f"Updated project {project_id} by user {user_id}")
        return project
    
    @staticmethod
    def delete_project(db: Session, project_id: int, user_id: str, user_name: Optional[str]) -> bool:
        """Delete a project"""
        project = ProjectService.get_project(db, project_id)
        
        if not project:
            return False
        
        # Log deletion before deleting
        ProjectService._log_activity(
            db, project_id, user_id, user_name, "deleted_project"
        )
        
        db.delete(project)
        db.commit()
        
        logger.info(f"Deleted project {project_id} by user {user_id}")
        return True
    
    @staticmethod
    def create_component(
        db: Session,
        project_id: int,
        user_id: str,
        user_name: Optional[str],
        component_data: ComponentCreate
    ) -> Optional[Component]:
        """Create a component for a project"""
        # Verify project exists
        project = ProjectService.get_project(db, project_id)
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
        db.flush()
        
        # Log component creation
        component_name = f"{component_data.component_type}_{component_data.component_index or 1}"
        ProjectService._log_activity(
            db, project_id, user_id, user_name,
            "created_component", component_name
        )
        
        db.commit()
        db.refresh(component)
        
        return component
    
    @staticmethod
    def update_component(
        db: Session,
        component_id: int,
        user_id: str,
        user_name: Optional[str],
        component_data: ComponentUpdate
    ) -> Optional[Component]:
        """Update a component"""
        component = db.query(Component).filter(
            Component.id == component_id
        ).first()
        
        if not component:
            return None
        
        update_data = component_data.model_dump(exclude_unset=True)
        
        # Track changes
        component_name = f"{component.component_type}_{component.component_index or 1}"
        
        for field, value in update_data.items():
            old_value = getattr(component, field, None)
            if old_value != value:
                ProjectService._log_activity(
                    db, component.project_id, user_id, user_name,
                    f"updated_component", component_name,
                    str(old_value), str(value)
                )
            setattr(component, field, value)
        
        db.commit()
        db.refresh(component)
        
        return component
    
    @staticmethod
    def add_translation(
        db: Session,
        component_id: int,
        user_id: str,
        user_name: Optional[str],
        language_code: str,
        translated_content: str
    ) -> Optional[Translation]:
        """Add a translation for a component"""
        component = db.query(Component).filter(
            Component.id == component_id
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
            old_content = existing.translated_content
            existing.translated_content = translated_content
            
            # Log update
            component_name = f"{component.component_type}_{component.component_index or 1}"
            ProjectService._log_activity(
                db, component.project_id, user_id, user_name,
                f"updated_translation_{language_code}", component_name
            )
            
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
        
        # Log creation
        component_name = f"{component.component_type}_{component.component_index or 1}"
        ProjectService._log_activity(
            db, component.project_id, user_id, user_name,
            f"added_translation_{language_code}", component_name
        )
        
        db.commit()
        db.refresh(translation)
        
        return translation
    
    @staticmethod
    def save_generated_content(
        db: Session,
        project_id: int,
        user_id: str,
        user_name: Optional[str],
        components_data: List[dict]
    ) -> List[Component]:
        """
        Save or update generated components in batch
        This replaces all existing components for the project
        """
        # Verify project exists
        project = ProjectService.get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Delete existing components (cascade will delete translations)
        db.query(Component).filter(Component.project_id == project_id).delete()
        db.flush()
        
        saved_components = []
        
        for comp_data in components_data:
            # Create component
            component = Component(
                project_id=project_id,
                component_type=comp_data["component_type"],
                component_index=comp_data.get("component_index"),
                generated_content=comp_data["generated_content"],
                component_url=comp_data.get("component_url"),
                image_id=comp_data.get("image_id")
            )
            
            db.add(component)
            db.flush()  # Get component ID
            
            # Add translations if provided
            translations_dict = comp_data.get("translations", {})
            for lang_code, translated_text in translations_dict.items():
                translation = Translation(
                    component_id=component.id,
                    language_code=lang_code,
                    translated_content=translated_text
                )
                db.add(translation)
            
            saved_components.append(component)
        
        # Log activity
        ProjectService._log_activity(
            db, project_id, user_id, user_name,
            "saved_generated_content",
            None, None, f"{len(saved_components)} components"
        )
        
        db.commit()
        
        # Refresh all components to get relationships
        for component in saved_components:
            db.refresh(component)
        
        logger.info(f"Saved {len(saved_components)} components for project {project_id}")
        return saved_components
    
    @staticmethod
    def get_activity_log(db: Session, project_id: int, limit: int = 50) -> List[ActivityLog]:
        """Get recent activity for a project"""
        logs = db.query(ActivityLog).filter(
            ActivityLog.project_id == project_id
        ).order_by(
            ActivityLog.created_at.desc()
        ).limit(limit).all()
        
        return logs
