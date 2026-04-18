from abc import ABC, abstractmethod
from typing import Any

from app.schemas.agent import AgentResponse

AgentPayload = dict[str, Any]

class BaseAgent(ABC):
    """Common contract for automation agents."""

    name: str = "base"

    @abstractmethod
    async def run(self, payload: AgentPayload) -> AgentResponse:
        """Execute the agent with a payload."""
        raise NotImplementedError

    def build_response(
        self,
        payload: AgentPayload,
        output: AgentPayload,
        status: str = "success",
    ) -> AgentResponse:
        return AgentResponse(
            agent=self.name,
            status=status,
            input=dict(payload),
            output=output,
        )
