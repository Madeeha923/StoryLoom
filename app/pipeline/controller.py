import logging
from time import perf_counter
from typing import Any, Sequence

from app.agents.base import AgentPayload, BaseAgent
from app.schemas.agent import AgentResponse

logger = logging.getLogger(__name__)


class PipelineController:
    """Executes agents sequentially with logging and graceful error handling."""

    def __init__(self, agents: Sequence[BaseAgent]) -> None:
        self.agents = list(agents)

    async def execute(self, payload: AgentPayload) -> dict[str, Any]:
        working_payload: AgentPayload = dict(payload)
        stage_results: dict[str, dict[str, Any]] = {}
        stage_logs: list[dict[str, Any]] = []
        pipeline_errors: list[dict[str, Any]] = []

        for position, agent in enumerate(self.agents, start=1):
            stage_name = agent.name
            logger.info("Starting pipeline stage '%s' (%s/%s)", stage_name, position, len(self.agents))
            started_at = perf_counter()

            try:
                result = await agent.run(working_payload)
                duration_ms = round((perf_counter() - started_at) * 1000, 2)

                stage_results[stage_name] = self._serialize_agent_response(result)
                stage_logs.append(
                    {
                        "stage": stage_name,
                        "event": "completed",
                        "status": result.status,
                        "duration_ms": duration_ms,
                    }
                )

                if result.status == "success":
                    logger.info(
                        "Completed pipeline stage '%s' successfully in %sms",
                        stage_name,
                        duration_ms,
                    )
                else:
                    logger.warning(
                        "Pipeline stage '%s' completed with status '%s' in %sms",
                        stage_name,
                        result.status,
                        duration_ms,
                    )
                    pipeline_errors.append(
                        {
                            "stage": stage_name,
                            "type": "agent_status",
                            "status": result.status,
                            "message": f"Stage returned non-success status '{result.status}'.",
                        }
                    )

                working_payload.update(result.output)
                working_payload["last_completed_stage"] = stage_name
                working_payload[f"{stage_name}_status"] = result.status
            except Exception as exc:
                duration_ms = round((perf_counter() - started_at) * 1000, 2)
                logger.exception(
                    "Pipeline stage '%s' failed after %sms",
                    stage_name,
                    duration_ms,
                )

                error_message = str(exc)
                error_response = AgentResponse(
                    agent=stage_name,
                    status="error",
                    input=self._sanitize_value(working_payload),
                    output={"error": error_message},
                )
                stage_results[stage_name] = self._serialize_agent_response(error_response)
                stage_logs.append(
                    {
                        "stage": stage_name,
                        "event": "failed",
                        "status": "error",
                        "duration_ms": duration_ms,
                        "message": error_message,
                    }
                )
                pipeline_errors.append(
                    {
                        "stage": stage_name,
                        "type": "exception",
                        "status": "error",
                        "message": error_message,
                    }
                )
                working_payload[f"{stage_name}_error"] = error_message
                working_payload["last_failed_stage"] = stage_name
                continue

        registrar_output = stage_results.get("registrar", {}).get("output", {})
        pipeline_status = self._determine_pipeline_status(stage_results)
        logger.info("Pipeline finished with status '%s'", pipeline_status)

        return {
            "status": pipeline_status,
            "stages": stage_results,
            "stage_logs": stage_logs,
            "pipeline_errors": pipeline_errors,
            "ready_for_upload": registrar_output.get("ready_for_upload", False),
            "upload_package": registrar_output.get("upload_package", {}),
        }

    def _determine_pipeline_status(
        self, stage_results: dict[str, dict[str, Any]]
    ) -> str:
        statuses = [stage.get("status", "success") for stage in stage_results.values()]
        if any(status == "error" for status in statuses):
            return "error"
        if any(status in {"partial", "invalid"} for status in statuses):
            return "partial"
        return "success"

    def _serialize_agent_response(
        self, response: AgentResponse
    ) -> dict[str, Any]:
        return {
            "agent": response.agent,
            "status": response.status,
            "input": self._sanitize_value(response.input),
            "output": self._sanitize_value(response.output),
        }

    def _sanitize_value(self, value: Any) -> Any:
        if isinstance(value, (bytes, bytearray)):
            return f"<binary:{len(value)} bytes>"
        if isinstance(value, dict):
            return {str(key): self._sanitize_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._sanitize_value(item) for item in value]
        if isinstance(value, tuple):
            return [self._sanitize_value(item) for item in value]
        return value


def build_default_pipeline_controller() -> PipelineController:
    from app.agents.copywriter_agent import CopywriterAgent
    from app.agents.historian_agent import HistorianAgent
    from app.agents.image_generator_agent import ImageGeneratorAgent
    from app.agents.input_agent import InputAgent
    from app.agents.registrar_agent import RegistrarAgent
    from app.agents.studio_agent import StudioAgent
    from app.agents.visionary_agent import VisionaryAgent

    return PipelineController(
        [
            InputAgent(),
            VisionaryAgent(),
            HistorianAgent(),
            CopywriterAgent(),
            StudioAgent(),
            ImageGeneratorAgent(),
            RegistrarAgent(),
        ]
    )
