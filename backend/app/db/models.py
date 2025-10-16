"""
Database models for Mosaico Platform
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, ARRAY
from sqlalchemy.orm import relationship
from app.db.base import Base


class Project(Base):
    """
    Represents one email campaign project
    One project = one campaign with multiple components
    """
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    brief_text = Column(Text)  # Creative prompt/instructions
    structure = Column(JSON, nullable=False)  # [{component: "body", count: 2}, ...]
    tone = Column(String(50))
    target_languages = Column(ARRAY(String))  # ['it', 'fr', 'de', ...]
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    components = relationship("Component", back_populates="project", cascade="all, delete-orphan")
    images = relationship("Image", back_populates="project", cascade="all, delete-orphan")


class Image(Base):
    """
    Uploaded images for email campaigns
    """
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(255), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    gcs_path = Column(String(500), nullable=False)  # Full GCS path (gs://bucket/path)
    gcs_public_url = Column(String(500))  # Public URL for accessing the image
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="images")
    components = relationship("Component", back_populates="image")


class Component(Base):
    """
    Individual email components (subject, body_1, cta_1, etc.)
    """
    __tablename__ = "components"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    component_type = Column(String(50), nullable=False)  # "subject", "body", "cta", etc.
    component_index = Column(Integer)  # 1, 2, 3 for body_1, body_2, etc. (null for unique components)
    generated_content = Column(Text)  # Original language content
    component_url = Column(String(500))  # Optional URL for this component (CTA link, product page, etc.)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="SET NULL"))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="components")
    image = relationship("Image", back_populates="components")
    translations = relationship("Translation", back_populates="component", cascade="all, delete-orphan")


class Translation(Base):
    """
    Translations for each component
    """
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, index=True)
    component_id = Column(Integer, ForeignKey("components.id", ondelete="CASCADE"), nullable=False)
    language_code = Column(String(10), nullable=False)  # "it", "fr", "de", etc.
    translated_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    component = relationship("Component", back_populates="translations")

