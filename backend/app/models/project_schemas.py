"""
Pydantic schemas for Project-related API endpoints
"""
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional


# ===== Project Schemas =====

class ProjectStatus(str, Enum):
    in_progress = "in_progress"
    approved = "approved"

class SectionStructureCreate(BaseModel):
    """A section in the email structure"""
    key: str = Field(..., description="Unique identifier for the section (e.g., 'section_1')")
    name: str = Field(..., description="Display name for the section (e.g., 'Hero Section')")
    components: List[str] = Field(..., description="List of component types in this section (e.g., ['image', 'title', 'cta'])")

class ProjectCreate(BaseModel):
    """Request to create a new project"""
    name: str = Field(..., min_length=1, max_length=255)
    brief_text: Optional[str] = None
    structure: List[SectionStructureCreate]
    tone: Optional[str] = None
    target_languages: List[str] = Field(default_factory=list)
    labels: List[str] = Field(default_factory=list)
    status: ProjectStatus = ProjectStatus.in_progress


class ProjectUpdate(BaseModel):
    """Request to update a project"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    brief_text: Optional[str] = None
    structure: Optional[List[SectionStructureCreate]] = None
    tone: Optional[str] = None
    target_languages: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    status: Optional[ProjectStatus] = None


class ProjectResponse(BaseModel):
    """Project response"""
    id: int
    name: str
    brief_text: Optional[str]
    structure: List[dict]
    tone: Optional[str]
    target_languages: List[str]
    labels: List[str]
    status: ProjectStatus
    
    # Audit fields
    created_by_user_id: Optional[str]
    created_by_user_name: Optional[str]
    updated_by_user_id: Optional[str]
    updated_by_user_name: Optional[str]
    
    created_at: datetime
    updated_at: datetime
    
    # Generated content (eagerly loaded)
    components: List["ComponentResponse"] = []
    images: List["ImageResponse"] = []
    
    class Config:
        from_attributes = True


# ===== Component Schemas =====

class ComponentCreate(BaseModel):
    """Request to create a component"""
    component_type: str
    component_index: Optional[int] = None
    generated_content: Optional[str] = None
    component_url: Optional[str] = None
    image_id: Optional[int] = None


class ComponentUpdate(BaseModel):
    """Request to update a component"""
    generated_content: Optional[str] = None
    component_url: Optional[str] = None
    image_id: Optional[int] = None


class TranslationResponse(BaseModel):
    """Translation for a component"""
    id: int
    language_code: str
    translated_content: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ComponentResponse(BaseModel):
    """Component response with translations"""
    id: int
    project_id: int
    section_key: str
    section_order: int
    component_type: str
    component_index: Optional[int]
    generated_content: Optional[str]
    component_url: Optional[str]
    image_id: Optional[int]
    created_at: datetime
    translations: List[TranslationResponse] = []
    
    class Config:
        from_attributes = True


# ===== Image Schemas =====

class ImageResponse(BaseModel):
    """Image metadata response"""
    id: int
    project_id: int
    filename: str
    gcs_path: str
    gcs_public_url: Optional[str]
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


# ===== Generation Schemas =====

class GenerateProjectContentRequest(BaseModel):
    """Request to generate content for a project"""
    count: int = Field(1, ge=1, le=5, description="Number of variations")
    image_urls: Optional[List[str]] = Field(default_factory=list, description="Optional image URLs to use as context")


class GenerateProjectContentResponse(BaseModel):
    """Response from generating content"""
    project_id: int
    components: List[ComponentResponse]


# ===== Translation Schemas =====

class TranslateProjectRequest(BaseModel):
    """Request to translate all project components"""
    languages: Optional[List[str]] = None  # If None, use project's target_languages


class TranslateProjectResponse(BaseModel):
    """Response from translating project"""
    project_id: int
    components: List[ComponentResponse]


# ===== Export Schemas =====

class ExportToSheetsRequest(BaseModel):
    """Request to export project to Google Sheets"""
    sheet_url: str = Field(..., description="Google Sheets URL")
    export_mode: str = Field("new_sheet", description="'new_sheet' or 'append'")
    include_metadata: bool = Field(True, description="Include character counts and metadata")


class ExportToSheetsResponse(BaseModel):
    """Response from exporting to sheets"""
    success: bool
    sheet_url: str
    message: str


# ===== Save Generated Content Schemas =====

class SavedComponentCreate(BaseModel):
    """Component data to save"""
    component_type: str
    component_index: Optional[int] = None
    generated_content: str
    component_url: Optional[str] = None
    image_id: Optional[int] = None
    translations: dict = Field(default_factory=dict, description="Dict of language_code -> translated_content")


class SaveGeneratedContentRequest(BaseModel):
    """Request to save generated components"""
    components: List[SavedComponentCreate]


class SaveGeneratedContentResponse(BaseModel):
    """Response from saving components"""
    project_id: int
    saved_count: int
    components: List[ComponentResponse]


# ===== Activity Log Schemas =====

class ActivityLogResponse(BaseModel):
    """Activity log entry"""
    id: int
    project_id: int
    user_id: str
    user_name: Optional[str]
    action: str
    field_changed: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

