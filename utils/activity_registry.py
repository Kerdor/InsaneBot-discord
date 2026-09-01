from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActivityDefinition:
    """Static definition of an Activity supported by InsaneBot."""

    key: str
    name: str
    status: str


ACTIVITIES: dict[str, ActivityDefinition] = {
    "snake": ActivityDefinition(
        key="snake",
        name="Snake",
        status="initial",
    ),
    "sudoku": ActivityDefinition(
        key="sudoku",
        name="Sudoku",
        status="initial",
    ),
    "wordle": ActivityDefinition(
        key="wordle",
        name="Wordle",
        status="initial",
    ),
    "2048": ActivityDefinition(
        key="2048",
        name="2048",
        status="future",
    ),
    "minesweeper": ActivityDefinition(
        key="minesweeper",
        name="Minesweeper",
        status="future",
    ),
    "tetris": ActivityDefinition(
        key="tetris",
        name="Tetris",
        status="future",
    ),
    "flappy_bird": ActivityDefinition(
        key="flappy_bird",
        name="Flappy Bird",
        status="future",
    ),
    "connect_four": ActivityDefinition(
        key="connect_four",
        name="Connect Four",
        status="future",
    ),
    "chess": ActivityDefinition(
        key="chess",
        name="Chess",
        status="future",
    ),
    "checkers": ActivityDefinition(
        key="checkers",
        name="Checkers",
        status="future",
    ),
}


def get_activity(activity_key: str) -> ActivityDefinition | None:
    """Return the registered Activity definition for a key."""
    return ACTIVITIES.get(activity_key)


def is_initial_activity(activity_key: str) -> bool:
    """Return whether an Activity belongs to the initial release scope."""
    activity = get_activity(activity_key)
    return activity is not None and activity.status == "initial"
