from typing import Dict, Any, List
from dataclasses import dataclass, field

@dataclass
class CapabilityTrace:
    score: float = 0.0
    best_role_evidence: str = ""
    ownership: float = 0.0
    production: float = 0.0
    raw_evidence_hits: int = 0
    exact_matches: List[str] = field(default_factory=list)

@dataclass
class BehaviorTrace:
    intent_score: float = 1.0
    reachability_score: float = 1.0
    demand_score: float = 1.0
    reliability_score: float = 1.0
    trust_score: float = 1.0
    logistics_score: float = 1.0
    final_multiplier: float = 1.0

@dataclass
class CredibilityTrace:
    consistency_score: int = 100
    credibility_score: int = 100
    final_multiplier: float = 1.0
    flags: List[str] = field(default_factory=list)

@dataclass
class RisksTrace:
    availability_penalty: float = 0.0
    domain_penalty: float = 0.0
    flags: List[str] = field(default_factory=list)

@dataclass
class Trace:
    capabilities: Dict[str, CapabilityTrace] = field(default_factory=dict)
    behavior: BehaviorTrace = field(default_factory=BehaviorTrace)
    credibility: CredibilityTrace = field(default_factory=CredibilityTrace)
    risks: RisksTrace = field(default_factory=RisksTrace)
    gates: List[str] = field(default_factory=list)
    top_strengths: List[str] = field(default_factory=list)
    jd_matches: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    behavior_strengths: List[str] = field(default_factory=list)
    technical_fit: float = 0.0
    final_score: float = 0.0
    reasoning_facts: List[str] = field(default_factory=list)
