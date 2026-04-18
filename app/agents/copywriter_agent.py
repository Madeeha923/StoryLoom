from app.agents.base import AgentPayload, BaseAgent
from app.schemas.agent import AgentResponse


class CopywriterAgent(BaseAgent):
    """Generates premium, story-led product copy from multi-agent context."""

    name = "copywriter"

    async def run(self, payload: AgentPayload) -> AgentResponse:
        source_product_name = str(payload.get("product_name", "Unnamed Product")).strip()
        cultural_topic = str(payload.get("cultural_topic", "")).strip()
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
            cultural_topic=cultural_topic,
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
        if color and color.lower() not in {"unknown", "not visible"} and color.lower() not in base_name.lower():
            descriptors.append(color.title())
        if (
            fabric
            and "not clearly" not in fabric.lower()
            and fabric.lower() not in base_name.lower()
        ):
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
        cultural_topic: str,
        descriptive_paragraph: str,
        visual_summary: str,
        background_context: str,
        cultural_context: str,
        tone: str,
    ) -> str:
        user_brief = input_summary or normalized_text
        cultural_snippet = background_context or cultural_context
        visual_snippet = descriptive_paragraph or visual_summary
        fallback_cultural = cultural_snippet.lower().startswith("no reliable wikipedia background")
        sentences: list[str] = []

        if cultural_snippet and not fallback_cultural:
            heritage_intro = self._build_heritage_intro(
                cultural_topic=cultural_topic,
                cultural_snippet=cultural_snippet,
                product_category=product_category,
            )
            sentences.append(heritage_intro)
            sentences.append(
                f"This particular piece carries that heritage into a contemporary {product_category} presentation through {self._build_visual_clause(visual_snippet, product_title)}."
            )
        else:
            sentences.append(
                f"{product_title} brings together traditional appeal and occasion-ready elegance in a refined {product_category} presentation."
            )
            if visual_snippet:
                sentences.append(
                    f"It stands out through {self._lowercase_first(visual_snippet)}."
                )

        if visual_snippet:
            sentences.append(
                f"The uniqueness of this piece comes through {self._lowercase_first(visual_snippet)}, giving it an elevated catalog presence."
            )
        if fallback_cultural:
            sentences.append(
                "Its appeal comes from the craftsmanship, textile character, and occasion-led elegance visible in the product itself."
            )
        if user_brief:
            sentences.append(
                f"For this version, the brief centers on {user_brief[:160].strip()}."
            )
        sentences.append(f"The overall tone remains {tone}, making it well suited for elevated catalog, boutique, and marketplace presentation.")
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

    def _normalize_sentence(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            return cleaned
        return cleaned if cleaned.endswith(".") else f"{cleaned}."

    def _lowercase_first(self, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) <= 1:
            return cleaned.lower()
        return cleaned[0].lower() + cleaned[1:]

    def _build_visual_clause(self, visual_snippet: str, product_title: str) -> str:
        cleaned = visual_snippet.strip()
        if not cleaned:
            return product_title
        return self._lowercase_first(cleaned)

    def _build_heritage_intro(
        self,
        *,
        cultural_topic: str,
        cultural_snippet: str,
        product_category: str,
    ) -> str:
        cleaned_topic = cultural_topic.strip() or product_category
        if cleaned_topic:
            topic_phrase = cleaned_topic[0].upper() + cleaned_topic[1:]
            return f"{topic_phrase} is known for its cultural heritage and textile craftsmanship. {self._normalize_sentence(cultural_snippet[:220])}"
        return self._normalize_sentence(cultural_snippet[:280])
