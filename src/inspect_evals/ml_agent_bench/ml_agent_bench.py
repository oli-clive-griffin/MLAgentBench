from inspect_ai import Task, eval, task
from inspect_ai.dataset import MemoryDataset, Sample

from inspect_evals.ml_agent_bench.adapter import research_agent
from inspect_evals.ml_agent_bench.args import Args

# BASE_DIR = Path("benchmarks")  #


# def house_prices():
#     # dir = BASE_DIR / "house_price"
#     # files={
#     #     f"{dir}/env/train.py": "train.py",
#     #     f"{dir}/env/test.py": "test.py",
#     # },
#     return


@task
def ml_agent_bench() -> Task:
    return Task(
        dataset=MemoryDataset(
            [
                Sample(
                    input="hello",
                    # input="please create a file called `results.txt` with the content 'results'",
                    # target=("results.txt", "results"),
                    # setup="python -m scripts.prepare",
                    # files={"train.csv": "train.csv", "test.csv": "test.csv"},
                    sandbox="local",
                    target="42",
                )
            ]
        ),
        solver=research_agent(Args()),
    )


if __name__ == "__main__":
    # vary the system prompt
    eval(ml_agent_bench(), model="openai/gpt-4o-mini", sandbox="local")
