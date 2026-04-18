from app.agents.base import AgentPayload, BaseAgent
from app.schemas.agent import AgentResponse
from app.services.wikipedia_client import WikipediaClient


class HistorianAgent(BaseAgent):
    """Fetches cultural and historical context from Wikipedia."""

    name = "historian"

    def __init__(self, wikipedia_client: WikipediaClient | None = None) -> None:
        self.wikipedia_client = wikipedia_client or WikipediaClient()

    async def run(self, payload: AgentPayload) -> AgentResponse:
        topic = self._resolve_product_name(payload)
        wikipedia_result = await self.wikipedia_client.fetch_cultural_summary(topic)
        lookup_error = wikipedia_result.get("error")
        enriched_background = self._build_background_context(
            product_name=topic,
            matched_title=wikipedia_result.get("matched_title"),
            description=wikipedia_result.get("description"),
            summary=wikipedia_result.get("summary"),
        )
        output = {
            "product_name": topic,
            "cultural_topic": topic,
            "background_context": enriched_background,
            "cultural_context": wikipedia_result.get("summary", ""),
            "wikipedia_description": wikipedia_result.get("description", ""),
            "wikipedia_title": wikipedia_result.get("matched_title"),
            "wikipedia_url": wikipedia_result.get("source_url"),
            "source": "wikipedia",
            "lookup_error": lookup_error,
            "lookup_status": "matched" if not lookup_error else "fallback_used",
        }
        status = "success" if topic else "partial"
        return self.build_response(payload, output, status=status)

    def _resolve_product_name(self, payload: AgentPayload) -> str:
        for key in ("product_name", "cultural_topic", "culture_hint", "product_origin"):
            value = str(payload.get(key, "")).strip()
            if value:
                return value
        return str(payload.get("normalized_text", "")).strip()

    def _build_background_context(
        self,
        *,
        product_name: str,
        matched_title: str | None,
        description: str | None,
        summary: str | None,
    ) -> str:
        if not summary:
            return (
                f"No reliable Wikipedia background was found for {product_name}. "
                "Use a neutral product description until cultural context is verified."
            )

        short_summary = self._shorten_summary(summary)
        parts = []
        if matched_title:
            if description:
                parts.append(f"{matched_title} is a {description}.")
            else:
                parts.append(f"{matched_title} provides relevant cultural context for {product_name}.")
        parts.append(short_summary)
        return " ".join(part.strip() for part in parts if part).strip()

    def _shorten_summary(self, summary: str) -> str:
        sentences = [segment.strip() for segment in summary.split(".") if segment.strip()]
        if not sentences:
            return summary.strip()
        return ". ".join(sentences[:2]).strip() + "."
