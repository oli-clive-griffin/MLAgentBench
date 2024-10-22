from inspect_ai.solver import Generate, Solver, TaskState, solver

from .environment import Environment
from .research_agent import ResearchAgent


@solver
def research_agent() -> Solver:
    async def run_research_agent(state: TaskState, generate: Generate) -> TaskState:
        agent = ResearchAgent()
        env = Environment()
        await agent.run(env)
        return 42


    return run_research_agent
