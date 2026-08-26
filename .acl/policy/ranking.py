"""Shared helpers for snippet ranking.

Ranked voting is the primary discovery signal. Agents upvote what worked;
usage and agent_rating amplify that signal into a composite score.
"""

from __future__ import annotations


def composite_score(votes: float = 0, usage_count: float = 0, agent_rating: float = 0.0) -> float:
    """Community rank score used by /api/v1/top?sort=score and CLI top --sort score.

    score = (agent_rating * 20) + votes + (usage_count * 0.25)
    """
    return (float(agent_rating or 0.0) * 20.0) + float(votes or 0) + (float(usage_count or 0) * 0.25)


# SQL expression matching composite_score() for sqlite ORDER BY
COMPOSITE_SCORE_SQL = "(COALESCE(agent_rating, 0) * 20 + COALESCE(votes, 0) + COALESCE(usage_count, 0) * 0.25)"
COMPOSITE_SCORE_SQL_ALIASED = (
    "(COALESCE(s.agent_rating, 0) * 20 + COALESCE(s.votes, 0) + COALESCE(s.usage_count, 0) * 0.25)"
)
