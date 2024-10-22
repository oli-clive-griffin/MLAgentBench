import os

from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.util import sandbox

from .args import Args
from .environment import Environment
from .research_agent import ResearchAgent
from .prepare_task import initialize_task_env


@solver
def research_agent(args: Args) -> Solver:
    async def run_research_agent(state: TaskState, generate: Generate) -> TaskState:
        await copy_env_into_sandbox(args.task)
        read_only_files = await initialize_task_env(
            args.work_dir, args.task, args.python
        )

        env = Environment(args, read_only_files)
        agent = ResearchAgent(args, env)
        await agent.run(env)
        return "42"

    return run_research_agent


async def copy_env_into_sandbox(task: str):
    sb = sandbox()

    task_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tasks", task)

    env_dir = os.path.join(task_dir, "env")
    env_files = os.listdir(env_dir)
    for fname in env_files:
        src_fname = os.path.join(env_dir, fname)
        dst_fname = os.path.join("env", fname)
        with open(src_fname, "r") as f:
            contents = f.read()
        print(f"writing {src_fname} to {dst_fname}")
        await sb.write_file(dst_fname, contents)

    scripts_dir = os.path.join(task_dir, "scripts")
    scripts_files = os.listdir(scripts_dir)
    for fname in scripts_files:
        src_fname = os.path.join(scripts_dir, fname)
        dst_fname = os.path.join("scripts", fname)
        with open(src_fname, "r") as f:
            contents = f.read()
        print(f"writing {src_fname} to {dst_fname}")
        await sb.write_file(dst_fname, contents)

    print("(sandbox) $ ls -la")
    print((await sb.exec(["ls", "-la"])).stdout)

    print("(sandbox) $ ls -la env")
    print((await sb.exec(["ls", "-la", "env"])).stdout)

    print("(sandbox) $ ls -la scripts")
    print((await sb.exec(["ls", "-la", "scripts"])).stdout)
