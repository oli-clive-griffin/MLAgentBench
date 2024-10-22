import argparse
import sys

from . import LLM, high_level_actions
from .agent import ResearchAgent
from .args import Args
from .environment import Environment


def run(args: Args):
    with Environment(args) as env:
        print("=====================================")
        print("Benchmark folder name: ", env.benchmark_folder_name)
        print("Research problem: ", env.research_problem)
        print(
            "Lower level actions enabled: ",
            [action.name for action in env.low_level_actions],
        )
        print(
            "High level actions enabled: ",
            [action.name for action in env.high_level_actions],
        )
        print("Read only files: ", env._read_only_files, file=sys.stderr)
        print("=====================================")

        agent = ResearchAgent(args, env)
        final_message = agent.run(env)
        print("=====================================")
        print("Final message: ", final_message)

    env.save("final")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # parser.add_argument("--task", type=str, default="debug", help="task name")
    parser.add_argument("--log-dir", type=str, default="./logs", help="log dir")
    parser.add_argument("--work-dir", type=str, default="./workspace", help="work dir")
    parser.add_argument("--max-steps", type=int, default=50, help="number of steps")
    parser.add_argument("--max-time", type=int, default=5 * 60 * 60, help="max time")
    parser.add_argument("--device", type=int, default=0, help="device id")
    parser.add_argument("--python", type=str, default="python", help="python command")
    parser.add_argument("--llm-name", type=str, default="claude-v1", help="llm name")

    # Temporarily fixed to "claude-v1"
    # parser.add_argument(
    #     "--fast-llm-name", type=str, default="claude-v1", help="llm name"
    # )
    # parser.add_argument(
    #     "--edit-script-llm-name", type=str, default="claude-v1", help="llm name"
    # )

    parser.add_argument(
        "--edit-script-llm-max-tokens", type=int, default=4000, help="llm max tokens"
    )
    parser.add_argument(
        "--agent-max-steps", type=int, default=50, help="max iterations for agent"
    )

    parser.add_argument(
        "--actions-remove-from-prompt",
        type=str,
        nargs="+",
        default=[],
        help="actions to remove in addition to the default ones: Read File, Write File, Append File, Retrieval from Research Log, Append Summary to Research Log, Python REPL, Edit Script Segment (AI)",
    )
    parser.add_argument(
        "--actions-add-to-prompt",
        type=str,
        nargs="+",
        default=[],
        help="actions to add",
    )
    parser.add_argument(
        "--valid-format-entires",
        type=str,
        nargs="+",
        default=[],
        help="valid format entries",
    )
    parser.add_argument(
        "--max-steps-in-context", type=int, default=3, help="max steps in context"
    )
    parser.add_argument(
        "--max-observation-steps-in-context",
        type=int,
        default=3,
        help="max observation steps in context",
    )
    parser.add_argument("--max-retries", type=int, default=5, help="max retries")

    args = Args.from_args(parser.parse_args())
    print(args, file=sys.stderr)
    LLM.FAST_MODEL = args.FIXED_FOR_NOW_fast_llm_name
    high_level_actions.EDIT_SCRIPT_MODEL = args.FIXED_FOR_NOW_edit_script_llm_name
    high_level_actions.EDIT_SCRIPT_MAX_TOKENS = args.edit_script_llm_max_tokens
    run(args)
