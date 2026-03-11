import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from lead_engine.db.models import SessionLocal, Campaign, Job, Lead, AgentLog
from lead_engine.core.key_manager import key_manager
from litellm import completion

logger = logging.getLogger(__name__)

class AssistantChat:
    """
    Intelligent chat assistant that can query system state and answer questions.
    """
    def __init__(self, model: str = "openrouter/anthropic/claude-3-haiku"):
        self.model = model
        self.system_prompt = """
        You are the 'Lead Intelligence Assistant'. Your role is to help the user manage their lead generation campaigns.
        You have access to real-time data from the database.
        Always be professional, concise, and helpful.
        If the user asks for status, use the provided tools to get accurate numbers.
        """

    def _get_campaign_summary(self, campaign_id: int) -> str:
        with SessionLocal() as db:
            campaign = db.query(Campaign).get(campaign_id)
            if not campaign:
                return f"Campaign with ID {campaign_id} not found."
            
            jobs = db.query(Job).filter_by(campaign_id=campaign_id).all()
            leads_count = db.query(Lead).filter_by(campaign_id=campaign_id).count()
            good_leads = db.query(Lead).filter_by(campaign_id=campaign_id, vetting_status='good').count()
            
            status_map = {j.id: j.status for j in jobs}
            
            summary = (
                f"Campaign: {campaign.name}\n"
                f"Status: {campaign.status}\n"
                f"Total Leads: {leads_count} ({good_leads} vetted as 'good')\n"
                f"Jobs: {len(jobs)} total. Detailed statuses: {status_map}"
            )
            return summary

    def _get_system_stats(self) -> str:
        with SessionLocal() as db:
            total_campaigns = db.query(Campaign).count()
            total_leads = db.query(Lead).count()
            active_jobs = db.query(Job).filter(Job.status.in_(['running', 'scraping'])).count()
            
            return f"System Stats: {total_campaigns} campaigns, {total_leads} total leads, {active_jobs} active search jobs."

    async def get_response(self, user_message: str, history: List[Dict] = None) -> str:
        """
        Processes a user message and returns an AI response, using tools if necessary.
        """
        # Simple implementation: inject system context into the prompt
        # In a real 'agent' setup we would use tool-calling, 
        # but for this MVP we'll combine context and let the LLM synthesize.
        
        context = self._get_system_stats()
        
        # Check if user is asking about a specific campaign by name
        with SessionLocal() as db:
            campaigns = db.query(Campaign).all()
            for c in campaigns:
                if c.name.lower() in user_message.lower():
                    context += f"\n\nContext for '{c.name}':\n{self._get_campaign_summary(c.id)}"

        messages = [
            {"role": "system", "content": f"{self.system_prompt}\n\nCurrent System Context:\n{context}"}
        ]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        try:
            # Ensure API key is in environment
            key_manager.inject_lite_llm_keys()
            
            response = completion(
                model=self.model,
                messages=messages,
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return f"I'm sorry, I encountered an error while processing your request: {str(e)[:100]}"

chat_assistant = AssistantChat()
