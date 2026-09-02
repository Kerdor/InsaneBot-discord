from __future__ import annotations

from dataclasses import dataclass

from databases.activities import get_result, init_activities, record_result
from databases.economy import add_reward_balance
from databases.xp import add_xp
from utils.activity_registry import get_activity


@dataclass(frozen=True)
class TrustedActivityResult:
    """A result that has already passed the external trust/verification boundary."""

    result_id: str
    activity_key: str
    guild_id: int
    user_id: int
    xp_reward: int = 0
    coin_reward: int = 0


def apply_trusted_result(result: TrustedActivityResult) -> bool:
    """Persist a trusted Activity result once and apply its configured rewards."""
    if not result.result_id.strip():
        raise ValueError("Activity result_id must not be empty")
    if not get_activity(result.activity_key):
        raise ValueError(f"Unknown Activity: {result.activity_key}")
    if result.guild_id <= 0 or result.user_id <= 0:
        raise ValueError("Activity guild_id and user_id must be positive")
    if result.xp_reward < 0 or result.coin_reward < 0:
        raise ValueError("Activity rewards cannot be negative")
    if result.xp_reward == 0 and result.coin_reward == 0:
        raise ValueError("Activity result must contain a reward")

    init_activities()
    existing = get_result(result.result_id)
    if existing is not None:
        if (
            existing["activity_key"] != result.activity_key
            or existing["guild_id"] != result.guild_id
            or existing["user_id"] != result.user_id
            or existing["xp_reward"] != result.xp_reward
            or existing["coin_reward"] != result.coin_reward
        ):
            raise ValueError("Activity result_id already exists with different result data")
        inserted = False
    else:
        inserted = record_result(
            result.result_id,
            result.activity_key,
            result.guild_id,
            result.user_id,
            result.xp_reward,
            result.coin_reward,
        )
        if not inserted:
            existing = get_result(result.result_id)
            if existing is None:
                raise RuntimeError("Activity result could not be recorded")
            if (
                existing["activity_key"] != result.activity_key
                or existing["guild_id"] != result.guild_id
                or existing["user_id"] != result.user_id
                or existing["xp_reward"] != result.xp_reward
                or existing["coin_reward"] != result.coin_reward
            ):
                raise ValueError("Activity result_id already exists with different result data")

    xp_applied = False
    coin_applied = False
    if result.xp_reward:
        _, xp_applied = add_xp(
            result.guild_id,
            result.user_id,
            result.xp_reward,
            reward_id=result.result_id,
        )
    if result.coin_reward:
        _, coin_applied = add_reward_balance(
            result.guild_id,
            result.user_id,
            result.coin_reward,
            result.result_id,
        )
    return inserted or xp_applied or coin_applied
