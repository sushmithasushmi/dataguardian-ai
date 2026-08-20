from typing import List, Literal, Optional

from pydantic import BaseModel


class InvestigationResult(BaseModel):
    incident_id: str
    root_cause: str
    failure_stage: str
    failed_component: str
    impact_summary: str
    evidence: List[str]
    runbook_used: str
    runbook_guidance: List[str]
    historical_incident_used: Optional[str]
    historical_similarity_score: Optional[int]
    recommended_action: str
    confidence: Literal["LOW", "MEDIUM", "HIGH"]