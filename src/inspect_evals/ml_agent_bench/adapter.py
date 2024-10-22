from inspect_ai.solver import Generate, TaskState
from inspect_ai.model import get_model

from .agent.research_agent import ResearchAgent
from .agent.environment import Environment


# implements the Solver protocol
async def run_research_agent(self, state: TaskState, generate: Generate) -> TaskState:
    agent = ResearchAgent()
    env = Environment()
    return agent.run(env) # :(

