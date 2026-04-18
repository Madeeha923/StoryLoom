from app.agents.base import AgentPayload, BaseAgent
from app.schemas.agent import AgentResponse


class InputAgent(BaseAgent):
    """Normalizes incoming text and voice content into one working brief."""

    name = "input"

    async def run(self, payload: AgentPayload) -> AgentResponse:
        text_input = str(payload.get("text", "")).strip()
        raw_voice_input = payload.get("voice_input", {}) or {}
        voice_input = raw_voice_input if isinstance(raw_voice_input, dict) else {}
        voice_transcript = str(
            payload.get("voice_transcript", "") or voice_input.get("transcript", "")
        ).strip()
        language = str(payload.get("language", "en")).strip() or "en"

        normalized_text = " ".join(
            segment for segment in [text_input, voice_transcript] if segment
        ).strip()

        active_channels = []
        if text_input:
            active_channels.append("text")
        if voice_transcript:
            active_channels.append("voice")

        status = "success" if normalized_text else "invalid"
        output = {
            "source_channels": active_channels,
            "normalized_text": normalized_text,
            "language": language,
            "voice_metadata": {
                "duration_seconds": voice_input.get("duration_seconds"),
                "format": voice_input.get("format"),
            },
            "input_summary": normalized_text[:240],
        }
        return self.build_response(payload, output, status=status)
