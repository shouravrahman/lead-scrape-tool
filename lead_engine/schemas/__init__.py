"""
Pydantic schemas for input validation.
Prevents injection attacks and malformed requests.
"""
from pydantic import BaseModel, Field, validator, field_validator
import re


class SearchQuery(BaseModel):
    """Validates user search intent"""
    intent: str = Field(..., min_length=3, max_length=500)
    max_leads: int = Field(default=50, ge=1, le=1000)
    sheet_id: str = Field(default=None, max_length=100)
    
    @field_validator('intent')
    @classmethod
    def validate_intent(cls, v):
        """Block SQL injection and code injection attempts"""
        if not isinstance(v, str):
            raise ValueError("Intent must be a string")
        
        dangerous_patterns = [
            'sql', 'drop', 'delete', 'insert', 'update', 'exec',
            'system', 'bash', 'python', 'eval', 'exec', '__import__',
            '--', ';', '/*', '*/', 'union', 'select'
        ]
        
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f"Query contains suspicious pattern: {pattern}")
        
        return v.strip()
    
    @field_validator('sheet_id')
    @classmethod
    def validate_sheet_id(cls, v):
        """Validate Google Sheet ID format"""
        if v is None:
            return v
        
        # Google Sheets IDs are 44 alphanumeric chars (base32)
        if not re.match(r'^[a-zA-Z0-9\-_]{40,50}$', v):
            raise ValueError("Invalid Google Sheet ID format")
        
        return v


class FilterQuery(BaseModel):
    """Validates lead filtering queries"""
    query: str = Field(..., min_length=1, max_length=200)
    
    @field_validator('query')
    @classmethod
    def validate_filter(cls, v):
        """Prevent injection in filter queries"""
        dangerous = ['sql', 'drop', 'delete', 'insert', '__', 'eval']
        v_lower = v.lower()
        
        if any(term in v_lower for term in dangerous):
            raise ValueError("Invalid filter query")
        
        return v.strip()


class JobConfig(BaseModel):
    """Configuration for a scraping job"""
    user_intent: str = Field(..., min_length=3, max_length=500)
    max_leads: int = Field(default=50, ge=1, le=1000)
    sheet_id: str = Field(default=None, max_length=100)
    user: str = Field(default="system", max_length=100)
    
    @field_validator('user_intent')
    @classmethod
    def validate_intent(cls, v):
        dangerous_patterns = [
            'sql', 'drop', 'delete', 'insert', 'exec', 'system',
            'bash', '__import__', 'eval', '--', ';'
        ]
        
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f"Invalid pattern in intent: {pattern}")
        
        return v.strip()


class LeadVetting(BaseModel):
    """Vetting status update for leads"""
    lead_id: int = Field(..., ge=1)
    status: str = Field(..., regex='^(good|junk|pending)$')
    feedback: str = Field(default="", max_length=1000)
    
    @field_validator('feedback')
    @classmethod
    def validate_feedback(cls, v):
        # Allow normal feedback text
        if len(v) > 1000:
            raise ValueError("Feedback too long (max 1000 chars)")
        return v
