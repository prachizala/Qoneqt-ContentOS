import logging
from typing import Optional, List
from pydantic import BaseModel, Field
from ai.llm_client import LLMClient

logger = logging.getLogger(__name__)

class ResearchResult(BaseModel):
    """
    Structured research outputs for topic grounding and hook angles.
    """
    core_concept: str = Field(description="Core concept or central theme of the topic.")
    key_facts: List[str] = Field(description="3-5 compelling facts, data points, or narrative angles.")
    hook_angles: List[str] = Field(description="2-3 scroll-stopping hook ideas for short-form video opening.")
    suggested_cta: str = Field(description="Targeted call-to-action suitable for Qoneqt platform engagement.")

class ResearchAgent:
    """
    AI Research Agent responsible for topic analysis, trend insights, and hook discovery.
    """
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    async def research_topic(
        self,
        topic: str,
        audience: str = "general",
        objective: Optional[str] = None,
        language: str = "en"
    ) -> ResearchResult:
        """
        Executes topic research and returns structured research insights.
        """
        logger.info(f"[ResearchAgent] Conducting research for topic: '{topic}'")

        system_prompt = (
            "You are a Senior Viral Content Strategist specializing in high-converting short-form vertical videos (Reels/Shorts/TikTok). "
            "Analyze the given topic and extract high-engagement hooks, core facts, and viral angles."
        )

        user_prompt = (
            f"Topic: {topic}\n"
            f"Target Audience: {audience}\n"
            f"Objective: {objective or 'Maximize audience engagement and retention'}\n"
            f"Language: {language}\n\n"
            f"Provide a structured research breakdown."
        )

        mock_fallback = ResearchResult(
            core_concept=f"Comprehensive insight into {topic}",
            key_facts=[
                f"90% of creators report higher engagement when covering {topic}.",
                f"Key innovation in {topic} is driving rapid adoption globally.",
                f"Understanding {topic} unlocks immediate competitive advantages."
            ],
            hook_angles=[
                f"Did you know this mind-blowing truth about {topic}?",
                f"Stop scrolling if you care about {topic}!",
                f"The secret behind {topic} that nobody is telling you."
            ],
            suggested_cta="Follow Qoneqt for daily AI content breakdowns & tech insights!"
        )

        return await self.llm_client.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=ResearchResult,
            mock_fallback=mock_fallback
        )
