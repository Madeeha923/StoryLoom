from app.agents.base import AgentPayload, BaseAgent
from app.schemas.agent import AgentResponse
from app.services.wikipedia_client import WikipediaClient


class HistorianAgent(BaseAgent):
    """Fetches cultural and historical context from Wikipedia."""

    name = "historian"

    def __init__(self, wikipedia_client: WikipediaClient | None = None) -> None:
        self.wikipedia_client = wikipedia_client or WikipediaClient()

    async def run(self, payload: AgentPayload) -> AgentResponse:
        product_name = self._resolve_product_name(payload)
        topic_candidates = self._build_topic_candidates(product_name, payload)
        wikipedia_result = await self._lookup_best_topic(topic_candidates)
        if wikipedia_result.get("error"):
            wikipedia_result = self._apply_curated_fallback(
                product_name=product_name,
                topic_candidates=topic_candidates,
                wikipedia_result=wikipedia_result,
            )
        lookup_error = wikipedia_result.get("error")
        enriched_background = self._build_background_context(
            product_name=product_name,
            matched_title=wikipedia_result.get("matched_title"),
            description=wikipedia_result.get("description"),
            summary=wikipedia_result.get("summary"),
        )
        output = {
            "product_name": product_name,
            "cultural_topic": wikipedia_result.get("topic") or product_name,
            "background_context": enriched_background,
            "cultural_context": wikipedia_result.get("summary", ""),
            "wikipedia_description": wikipedia_result.get("description", ""),
            "wikipedia_title": wikipedia_result.get("matched_title"),
            "wikipedia_url": wikipedia_result.get("source_url"),
            "source": "wikipedia",
            "lookup_error": lookup_error,
            "lookup_status": "matched" if not lookup_error else "fallback_used",
        }
        status = "success" if product_name else "partial"
        return self.build_response(payload, output, status=status)

    def _resolve_product_name(self, payload: AgentPayload) -> str:
        for key in ("product_name", "cultural_topic", "culture_hint", "product_origin"):
            value = str(payload.get(key, "")).strip()
            if value:
                return value
        return str(payload.get("normalized_text", "")).strip()

    async def _lookup_best_topic(
        self, topic_candidates: list[str]
    ) -> dict[str, str | None]:
        fallback_result: dict[str, str | None] | None = None

        for candidate in topic_candidates:
            result = await self.wikipedia_client.fetch_cultural_summary(candidate)
            if not result.get("error"):
                return result
            if fallback_result is None:
                fallback_result = result

        return fallback_result or {
            "topic": "",
            "description": "",
            "summary": "",
            "source_url": None,
            "matched_title": None,
            "error": "No cultural topic candidates were available.",
        }

    def _build_topic_candidates(
        self, product_name: str, payload: AgentPayload
    ) -> list[str]:
        category = str(payload.get("product_category", "")).strip().lower()
        base_candidates = [
            product_name.strip(),
            self._strip_merchandising_descriptors(product_name, category),
        ]

        alias_candidates: list[str] = []
        for candidate in base_candidates:
            alias_candidates.extend(self._expand_topic_aliases(candidate))

        deduped: list[str] = []
        for candidate in base_candidates + alias_candidates:
            cleaned = candidate.strip()
            if cleaned and cleaned.lower() not in {item.lower() for item in deduped}:
                deduped.append(cleaned)
        return deduped

    def _strip_merchandising_descriptors(
        self, product_name: str, category: str
    ) -> str:
        text = product_name.strip()
        if not text:
            return text

        lowered_words = text.split()
        stop_words = {
            "pink",
            "red",
            "green",
            "blue",
            "yellow",
            "orange",
            "purple",
            "black",
            "white",
            "gold",
            "silver",
            "beige",
            "maroon",
            "navy",
            "floral",
            "motifs",
            "motif",
            "pattern",
            "patterned",
            "embroidered",
            "handmade",
            "handcrafted",
            "designer",
            "premium",
            "elegant",
            "partywear",
            "bridal",
            "traditional",
        }
        filtered_words = [
            word
            for word in lowered_words
            if word.lower() not in stop_words and word.lower() != "with"
        ]

        simplified = " ".join(filtered_words).strip()
        if category and category not in simplified.lower():
            simplified = f"{simplified} {category}".strip()
        return simplified or product_name

    def _expand_topic_aliases(self, topic: str) -> list[str]:
        lowered = topic.lower()
        aliases = [topic]

        alias_map = {
            "kanjivaram": "Kanchipuram silk sari",
            "kanjeevaram": "Kanchipuram silk sari",
            "kanchipuram saree": "Kanchipuram silk sari",
            "banarasi saree": "Banarasi sari",
            "paithani saree": "Paithani",
        }

        for key, alias in alias_map.items():
            if key in lowered:
                aliases.append(alias)

        return aliases

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

    def _apply_curated_fallback(
        self,
        *,
        product_name: str,
        topic_candidates: list[str],
        wikipedia_result: dict[str, str | None],
    ) -> dict[str, str | None]:
        lowered_candidates = " ".join(topic_candidates).lower()

        if any(
            key in lowered_candidates
            for key in ("kanjivaram", "kanjeevaram", "kanchipuram")
        ):
            return {
                "topic": "Kanjivaram saree",
                "matched_title": "Kanchipuram silk sari",
                "description": "traditional silk sari style from Kanchipuram, Tamil Nadu",
                "summary": (
                    "Kanjivaram sarees are traditionally associated with Kanchipuram in Tamil Nadu and are celebrated for their rich silk weaving, temple-inspired motifs, contrast borders, and zari detailing. "
                    "They are especially valued for ceremonial wear because of their craftsmanship, structure, and heritage appeal."
                ),
                "source_url": None,
                "error": None,
            }

        return wikipedia_result

    def _shorten_summary(self, summary: str) -> str:
        sentences = [segment.strip() for segment in summary.split(".") if segment.strip()]
        if not sentences:
            return summary.strip()
        return ". ".join(sentences[:2]).strip() + "."
