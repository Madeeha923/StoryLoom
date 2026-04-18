from app.agents.base import AgentPayload, BaseAgent
from app.schemas.agent import AgentResponse


class CopywriterAgent(BaseAgent):
    """Generates premium, story-led product copy from multi-agent context."""

    name = "copywriter"

    async def run(self, payload: AgentPayload) -> AgentResponse:
        source_product_name = str(payload.get("product_name", "Unnamed Product")).strip()
        product_category = (
            str(payload.get("product_category", "lifestyle product")).strip()
            or "lifestyle product"
        )
        tone = (
            str(payload.get("tone", "premium and storytelling-based")).strip()
            or "premium and storytelling-based"
        )
        normalized_text = str(payload.get("normalized_text", "")).strip()
        input_summary = str(payload.get("input_summary", "")).strip()
        background_context = str(payload.get("background_context", "")).strip()
        cultural_context = str(payload.get("cultural_context", "")).strip()
        visual_summary = str(payload.get("visual_summary", "")).strip()
        descriptive_paragraph = str(payload.get("descriptive_paragraph", "")).strip()
        fabric = str(payload.get("fabric", "")).strip()
        color = str(payload.get("color", "")).strip()
        pattern = str(payload.get("pattern", "")).strip()

        product_title = self._build_product_title(
            source_product_name=source_product_name,
            product_category=product_category,
            color=color,
            fabric=fabric,
        )
        description = self._build_description(
            product_title=product_title,
            product_category=product_category,
            normalized_text=normalized_text,
            input_summary=input_summary,
            descriptive_paragraph=descriptive_paragraph,
            visual_summary=visual_summary,
            background_context=background_context,
            cultural_context=cultural_context,
            tone=tone,
        )
        bullet_highlights = self._build_bullet_highlights(
            product_category=product_category,
            fabric=fabric,
            color=color,
            pattern=pattern,
            background_context=background_context,
            normalized_text=normalized_text,
        )
        seo_tags = self._build_seo_tags(
            product_title=product_title,
            source_product_name=source_product_name,
            product_category=product_category,
            fabric=fabric,
            color=color,
            pattern=pattern,
        )

        output = {
            "product_name": source_product_name,
            "product_title": product_title,
            "product_description": description,
            "bullet_highlights": bullet_highlights,
            "seo_tags": seo_tags,
            "headline": f"{product_title} | Heritage-inspired luxury",
            "tone": tone,
            "seo_keywords": seo_tags,
        }
        return self.build_response(payload, output)

    def _build_product_title(
        self,
        *,
        source_product_name: str,
        product_category: str,
        color: str,
        fabric: str,
    ) -> str:
        base_name = source_product_name if source_product_name != "Unnamed Product" else ""
        descriptors = []
        if color and color.lower() not in {"unknown", "not visible"}:
            descriptors.append(color.title())
        if fabric and "not clearly" not in fabric.lower():
            descriptors.append(self._title_case_phrase(fabric))

        if base_name:
            title_parts = descriptors[:2] + [base_name]
            return " ".join(part for part in title_parts if part).strip()

        return " ".join(
            part for part in descriptors[:2] + [self._title_case_phrase(product_category)] if part
        ).strip() or "Curated Premium Product"

    def _build_description(
        self,
        *,
        product_title: str,
        product_category: str,
        normalized_text: str,
        input_summary: str,
        descriptive_paragraph: str,
        visual_summary: str,
        background_context: str,
        cultural_context: str,
        tone: str,
    ) -> str:
        user_brief = input_summary or normalized_text
        cultural_snippet = background_context or cultural_context
        visual_snippet = descriptive_paragraph or visual_summary

        sentences = [f"{product_title} is a premium {product_category} shaped with a refined, story-led point of view."]
        if visual_snippet:
            sentences.append(
                f"Visually, it stands out through {visual_snippet[0].lower() + visual_snippet[1:] if len(visual_snippet) > 1 else visual_snippet.lower()}."
            )
        if cultural_snippet:
            sentences.append(
                f"Its narrative draws from meaningful cultural context: {cultural_snippet[:220].strip()}"
                f"{'' if cultural_snippet[:220].strip().endswith('.') else '.'}"
            )
        if user_brief:
            sentences.append(
                f"Created for discerning customers, it answers the original brief with a polished expression of {user_brief[:160].strip()}."
            )
        sentences.append(
            f"The overall tone remains {tone}, making it suited for elevated catalog, boutique, and marketplace presentation."
        )
        return " ".join(sentences)

    def _build_bullet_highlights(
        self,
        *,
        product_category: str,
        fabric: str,
        color: str,
        pattern: str,
        background_context: str,
        normalized_text: str,
    ) -> list[str]:
        highlights = [f"Premium {product_category} with a storytelling-led presentation."]
        if fabric:
            highlights.append(f"Fabric: {fabric}.")
        if color:
            highlights.append(f"Color profile: {color}.")
        if pattern:
            highlights.append(f"Pattern detail: {pattern}.")
        if background_context:
            highlights.append(f"Cultural inspiration: {background_context[:140].strip()}{'' if background_context[:140].strip().endswith('.') else '.'}")
        elif normalized_text:
            highlights.append(f"Designed around the brief: {normalized_text[:140].strip()}{'' if normalized_text[:140].strip().endswith('.') else '.'}")
        return highlights[:5]

    def _build_seo_tags(
        self,
        *,
        product_title: str,
        source_product_name: str,
        product_category: str,
        fabric: str,
        color: str,
        pattern: str,
    ) -> list[str]:
        candidates = [
            product_title,
            source_product_name,
            product_category,
            fabric,
            color,
            pattern,
            "premium fashion",
            "storytelling product copy",
            "luxury e-commerce",
        ]
        tags: list[str] = []
        for candidate in candidates:
            cleaned = str(candidate).strip().lower()
            if cleaned and cleaned not in {"unnamed product", "lifestyle product"} and cleaned not in tags:
                tags.append(cleaned)
        return tags[:8]

    def _title_case_phrase(self, value: str) -> str:
        return " ".join(word.capitalize() for word in value.split())
