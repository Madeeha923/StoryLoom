from app.agents.base import BaseAgent
from app.pipeline.controller import (
    PipelineController,
    build_default_pipeline_controller,
)
from app.schemas.agent import AgentResponse


class OrchestrationAgent(BaseAgent):
    """Coordinates the full e-commerce automation agent workflow."""

    name = "orchestration"

    def __init__(self, controller: PipelineController | None = None) -> None:
        self.controller = controller or build_default_pipeline_controller()

    async def run(self, payload: dict[str, object]) -> AgentResponse:
        output = await self.controller.execute(payload)
        return self.build_response(payload, output, status=output["status"])
