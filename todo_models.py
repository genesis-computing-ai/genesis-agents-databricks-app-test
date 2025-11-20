"""
Pydantic models for TODO API validation and serialization.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class TodoCreate(BaseModel):
    """Model for creating a new TODO."""
    title: str = Field(..., min_length=1, max_length=255, description="TODO title")
    description: Optional[str] = Field(None, description="TODO description")
    priority: int = Field(2, ge=0, le=4, description="Priority: 0=Critical, 1=High, 2=Medium, 3=Low, 4=Backlog")
    due_date: Optional[datetime] = Field(None, description="Due date for the TODO")
    payload: Optional[dict] = Field(None, description="JSON payload for additional data")
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate title is not empty after stripping."""
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()


class TodoUpdate(BaseModel):
    """Model for updating an existing TODO."""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="TODO title")
    description: Optional[str] = Field(None, description="TODO description")
    completed: Optional[bool] = Field(None, description="Completion status")
    priority: Optional[int] = Field(None, ge=0, le=4, description="Priority: 0=Critical, 1=High, 2=Medium, 3=Low, 4=Backlog")
    due_date: Optional[datetime] = Field(None, description="Due date for the TODO")
    payload: Optional[dict] = Field(None, description="JSON payload for additional data")
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate title is not empty after stripping if provided."""
        if v is not None and not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip() if v else None


class TodoResponse(BaseModel):
    """Model for TODO API responses."""
    id: int
    title: str
    description: Optional[str]
    completed: bool
    priority: int
    due_date: Optional[datetime]
    payload: Optional[dict]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

