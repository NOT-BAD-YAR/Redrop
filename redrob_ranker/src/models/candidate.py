from typing import TypedDict, List, Optional, Dict, Any
from .trace import Trace

class CareerRole(TypedDict, total=False):
    company: str
    title: str
    start_date: str
    end_date: Optional[str]
    duration_months: int
    is_current: bool
    industry: str
    company_size: str
    description: str
    start_ts: float
    end_ts: float

class Skill(TypedDict, total=False):
    name: str
    proficiency: str
    endorsements: int
    duration_months: int

class CandidateProfile(TypedDict, total=False):
    anonymized_name: str
    headline: str
    summary: str
    location: str
    country: str
    years_of_experience: float
    current_title: str
    current_company: str
    current_company_size: str
    current_industry: str

class Candidate(TypedDict, total=False):
    candidate_id: str
    profile: CandidateProfile
    career_history: List[CareerRole]
    education: List[Dict[str, Any]]
    skills: List[Skill]
    certifications: List[Dict[str, Any]]
    languages: List[Dict[str, Any]]
    redrob_signals: Dict[str, Any]
    trace: Trace
    final_score: float
