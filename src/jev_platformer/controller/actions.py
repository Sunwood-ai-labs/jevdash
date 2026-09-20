"""Controller action definitions."""

from enum import Enum
from typing import List


class Action(str, Enum):
    NOOP = "noop"
    RIGHT = "right"
    RIGHT_RUN = "right_run"
    RIGHT_JUMP = "right_jump"
    RIGHT_RUN_JUMP = "right_run_jump"
    JUMP = "jump"
    LEFT = "left"


ALL_ACTIONS: List[str] = [
    Action.NOOP.value,
    Action.RIGHT.value,
    Action.RIGHT_RUN.value,
    Action.RIGHT_JUMP.value,
    Action.RIGHT_RUN_JUMP.value,
    Action.JUMP.value,
    Action.LEFT.value,
]
