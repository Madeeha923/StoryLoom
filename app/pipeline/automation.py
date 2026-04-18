from app.pipeline.controller import (
    PipelineController,
    build_default_pipeline_controller,
)


class EcommerceAutomationPipeline:
    """Pipeline that executes the full multi-agent automation workflow."""

    def __init__(self, controller: PipelineController | None = None) -> None:
        self.controller = controller or build_default_pipeline_controller()

    async def execute(self, payload: dict[str, object]) -> dict[str, object]:
        return await self.controller.execute(payload)
