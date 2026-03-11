import os
import logging
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from lead_engine.tools.search_tools import search_internet, scrape_website
from lead_engine.core.key_manager import key_manager
from lead_engine.schemas.crew_schemas import FinalLeadList

logger = logging.getLogger(__name__)

@CrewBase
class LeadGenerationCrew():
    """Lead Generation Crew for finding, extracting, and scoring leads."""
    
    # Paths to the yaml configs
    agents_config = '../config/agents.yaml'
    tasks_config = '../config/tasks.yaml'
    
    def __init__(self, config_overrides: dict = None):
        self.config_overrides = config_overrides or {}
        # CrewAI @CrewBase normally loads these automatically, 
        # but we want to intercept and merge overrides.
        import yaml
        
        base_path = os.path.dirname(__file__)
        with open(os.path.join(base_path, self.agents_config), 'r') as f:
            self.agents_config = yaml.safe_load(f)
        with open(os.path.join(base_path, self.tasks_config), 'r') as f:
            self.tasks_config = yaml.safe_load(f)
            
        # Apply overrides (e.g., custom prompts or goals per campaign)
        if 'agents' in self.config_overrides:
            for agent_name, overrides in self.config_overrides['agents'].items():
                if agent_name in self.agents_config:
                    self.agents_config[agent_name].update(overrides)
                    
        if 'tasks' in self.config_overrides:
            for task_name, overrides in self.config_overrides['tasks'].items():
                if task_name in self.tasks_config:
                    self.tasks_config[task_name].update(overrides)

    @property
    def llm(self):
        if hasattr(self, '_llm'): return self._llm
        self._llm = key_manager.get_crewai_llm("openrouter")
        return self._llm

    @agent
    def planner(self) -> Agent:
        return Agent(
            config=self.agents_config['planner'],
            tools=[search_internet],
            llm=self.llm,
            verbose=True
        )

    @agent
    def extractor(self) -> Agent:
        return Agent(
            config=self.agents_config['extractor'],
            tools=[scrape_website],
            llm=self.llm,
            verbose=True
        )

    @agent
    def scorer(self) -> Agent:
        return Agent(
            config=self.agents_config['scorer'],
            llm=self.llm,
            verbose=True
        )

    @task
    def plan_search_task(self) -> Task:
        return Task(
            config=self.tasks_config['plan_search']
        )

    @task
    def scrape_and_extract_task(self) -> Task:
        return Task(
            config=self.tasks_config['scrape_and_extract']
        )

    @task
    def score_lead_task(self) -> Task:
        return Task(
            config=self.tasks_config['score_lead'],
            output_pydantic=FinalLeadList
        )

    @crew
    def crew(self) -> Crew:
        """Creates the LeadGeneration Crew"""
        return Crew(
            agents=self.agents, # Automatically accumulated by @agent decorator
            tasks=self.tasks,   # Automatically accumulated by @task decorator
            process=Process.sequential,
            verbose=True
        )
