import dataclasses
from dataclasses import dataclass
from argparse import Namespace
import json
from typing import Any, Callable, Coroutine


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        # if it is a function, use its string name
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        elif hasattr(o, "__call__"):
            return o.__name__
        elif isinstance(o, Namespace):
            return vars(o)

        return super().default(o)


class TooLongPromptError(Exception):
    pass


class LLMError(Exception):
    pass


class EnvException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


@dataclass(frozen=True)
class ActionInfo:
    name: str
    description: str
    usage: dict[str, str]
    return_value: str
    function: Callable[..., Coroutine[Any, Any, Any]]
    is_low_level: bool


@dataclass(frozen=True)
class Action:
    name: str
    args: dict[str, Any]


@dataclass(frozen=True)
class Step:
    action: Action
    observation: str  # What was returned
    timestamp: float  # When the action was taken


@dataclass(frozen=True)
class Trace:
    steps: list[Step]
    low_level_steps: list[Step]
    action_infos: dict[str, ActionInfo]
    task_description: str
