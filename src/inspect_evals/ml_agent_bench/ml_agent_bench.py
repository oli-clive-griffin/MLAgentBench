from pathlib import Path
from textwrap import dedent

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample, file_dataset
from inspect_ai.scorer import Score, Scorer, Target, accuracy, mean, scorer
from inspect_ai.solver import TaskState, basic_agent
from inspect_ai.tool import bash
from inspect_ai.util import sandbox

from inspect_evals.ml_agent_bench.benchmarks.house_price.scripts.eval import get_score

BASE_DIR = Path("benchmarks") # 


def house_prices():
    dir = BASE_DIR / "house_price"

    files={
        f"{dir}/env/train.py": "train.py",
        f"{dir}/env/test.py": "test.py",
    },

    return Sample(
        # input="please create a file called `results.txt` with the content 'results'",
        # target=("results.txt", "results"),
        setup="python -m scripts.prepare",
        files={"train.csv": "train.csv", "test.csv": "test.csv"},
        sandbox="local",
    )


@task
def ml_agent_bench():
    return Task(
        dataset=MemoryDataset([house_prices()]),
        solver=basic_agent(tools=[bash()]),
    )


@task
def demo():
    solver = basic_agent(tools=[bash()])

    @scorer(metrics=[mean(), accuracy()])
    def file_creation_scorer() -> Scorer:
        async def f(state: TaskState, target: Target) -> Score:
            fname, content = target.target

            res = await sandbox().exec(["cat", fname])
            if res.stdout.strip() == content:
                return Score(
                    value=1.0,
                    explanation="The file was created with the correct content.",
                )
            else:
                return Score(
                    value=0.0,
                    explanation="The file was not created with the correct content.",
                )

        return f

    def dataset():
        return MemoryDataset(
            [
                Sample(
                    input="please create a file called `hello.txt` with the content 'hello world'",
                    target=("hello.txt", "hello world"),
                ),
                Sample(
                    input="please create a file called `results.txt` with the content 'results'",
                    target=("results.txt", "results"),
                ),
            ]
        )

    return Task(
        dataset=dataset(),
        solver=solver,
        sandbox="local",
        scorer=file_creation_scorer(),
    )
