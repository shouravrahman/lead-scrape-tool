from pydantic import BaseModel, Field
from typing import List, Optional

class ExtractedLeadProfile(BaseModel):
    """Schema for the extraction agent's output"""
    name: Optional[str] = Field(None, description="The person's full name")
    company: Optional[str] = Field(None, description="The company they work for or founded")
    role: Optional[str] = Field(None, description="Their job title or role")
    email: Optional[str] = Field(None, description="Their email address, if found")
    linkedin_url: Optional[str] = Field(None, description="Their LinkedIn profile URL, if found")
    tech_stack: Optional[List[str]] = Field(default=[], description="Any technologies or tools mentioned")
    hiring_signal: bool = Field(default=False, description="True if there is evidence they are actively hiring")
    launch_signal: bool = Field(default=False, description="True if there is evidence they recently launched a product")
    source_url: str = Field(..., description="The URL where this information was found")

class ScoredLeadProfile(ExtractedLeadProfile):
    """Schema for the scoring agent's output"""
    score: float = Field(default=0.0, description="The calculated ICP score (out of 20)")
    vetting_status: Optional[str] = Field(None, description="Status of the lead: 'good' if score >= 15, otherwise left empty")

class FinalLeadList(BaseModel):
    """Schema for the final crew output"""
    leads: List[ScoredLeadProfile] = Field(default=[], description="List of completely extracted and scored leads")
