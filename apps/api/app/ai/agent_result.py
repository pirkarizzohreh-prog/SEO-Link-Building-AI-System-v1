from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentResult:
    """What every agent function returns to app/jobs/handlers.py: enough
    to fill in the `ai_jobs` row (output_payload/tokens_used/cost_estimate).
    All of the agent's actual DB writes (Keyword rows, Topic rows, ...)
    happen inside the agent function itself, flushed but not committed —
    the handler commits once, atomically, alongside the job's own status.
    """

    output_payload: dict[str, Any] = field(default_factory=dict)
    tokens_used: int = 0
    cost_estimate: float = 0.0
