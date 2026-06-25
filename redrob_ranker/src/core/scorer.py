import yaml
import os
from typing import Dict, Any

config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "weights.yaml")
with open(config_path, "r", encoding="utf-8") as f:
    WEIGHTS = yaml.safe_load(f)["technical_fit"]["capability_weights"]

def score_technical_fit(cand: Dict[str, Any], trace: Dict[str, Any]) -> None:
    """Stages 6-7: Capability Aggregation and Technical Fit"""
    score = 0.0
    for cap, cap_trace in trace["capabilities"].items():
        w = WEIGHTS.get(cap, 0)
        score += cap_trace["score"] * w
        
    trace["technical_fit"] = min(100.0, score)
