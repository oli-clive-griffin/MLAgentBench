import argparse
from dataclasses import dataclass, field


@dataclass
class Args:
    task: str = "cifar10"
    log_dir: str = "./logs"
    work_dir: str = "./workspace"
    max_steps: int = 50
    max_time: int = 5 * 60 * 60
    device: int = 0
    python: str = "python"
    llm_name: str = "claude-v1"
    agent_max_steps: int = 50
    FIXED_FOR_NOW_fast_llm_name: str = "claude-v1"
    FIXED_FOR_NOW_edit_script_llm_name: str = "claude-v1"
    edit_script_llm_max_tokens: int = 4000
    actions_remove_from_prompt: list[str] = field(default_factory=list)
    actions_add_to_prompt: list[str] = field(default_factory=list)
    retrieval: bool = False  # IDK
    valid_format_entires: list[str] = field(default_factory=list)
    max_steps_in_context: int = 3
    max_observation_steps_in_context: int = 3
    max_retries: int = 5

    @staticmethod
    def from_args(args: argparse.Namespace):
        return Args(**args.__dict__)
