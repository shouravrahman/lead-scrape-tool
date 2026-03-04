from typing import List, Dict, Any
from lead_engine.db.models import SessionLocal, Lead

class ICPScoringAgent:
    """
    Evaluates leads based on predefined ICP criteria and learned feedback.
    Features: Hiring Pattern Detection, Builder Intent Scoring.
    """
    
    def __init__(self):
        # Base weights
        self.weights = {
            "role": 5,
            "company": 5,
            "hiring": 6,       # Increased for hire intent
            "launch": 4,       # New: Launch momentum
            "tech_stack": 7
        }

    def _get_learned_patterns(self):
        """
        Analyses 'good' vs 'junk' leads to adjust weights dynamically.
        """
        db = SessionLocal()
        try:
            good_leads = db.query(Lead).filter(Lead.vetting_status == 'good').limit(50).all()
            learned_boosts = []
            for lead in good_leads:
                if lead.tech_stack: learned_boosts.extend(lead.tech_stack)
            return list(set(learned_boosts))
        finally:
            db.close()

    def score_lead(self, lead: Lead) -> float:
        score = 0.0
        
        # 1. Role Check (Higher for Founders)
        high_value_roles = ["founder", "ceo", "cto", "owner", "partner", "maker"]
        if lead.name and any(role in lead.name.lower() for role in high_value_roles):
            score += self.weights["role"]
            
        # 2. Company Check
        if lead.company:
            score += self.weights["company"]
            
        # 3. Hiring Signal Detection (High Intent)
        # Check raw data or extracted hiring_status
        is_hiring = False
        if hasattr(lead, 'raw_data') and lead.raw_data:
            raw_str = str(lead.raw_data).lower()
            if any(k in raw_str for k in ["hiring", "jobs", "careers", "career"]):
                is_hiring = True
        
        if is_hiring:
            score += self.weights["hiring"]
            
        # 4. Launch Momentum Check
        if hasattr(lead, 'raw_data') and lead.raw_data:
            raw_str = str(lead.raw_data).lower()
            if any(k in raw_str for k in ["launch", "product hunt", "beta", "show hn"]):
                score += self.weights["launch"]
            
        # 5. Tech Stack Check (with Learned Boosts)
        learned_tech = self._get_learned_patterns()
        if lead.tech_stack:
            for tech in lead.tech_stack:
                score += 1.5 
                if tech in learned_tech:
                    score += 2.0 
                    
        return min(score, 20.0)
