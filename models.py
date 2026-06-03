from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class BusinessProfile(BaseModel):
    company_name: str
    vertical: str # ecommerce, saas, professional_services, healthcare_clinic, home_services [cite: 304]
    location: str
    employee_count_range: str

class OpportunityMatch(BaseModel):
    rank: int
    opportunity_id: str
    opportunity_name: str
    fit_strength: str # strong, moderate, exploratory [cite: 351]
    why_it_surfaced: str
    questions_to_answer: List[str]

class AuditObject(BaseModel):
    audit_id: str
    call_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    business: BusinessProfile
    opportunity_areas_identified: List[OpportunityMatch]
    audit_summary_narrative: str [cite: 1010]