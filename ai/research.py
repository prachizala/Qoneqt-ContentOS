from pydantic import BaseModel
from typing import List

class TopicResearchResult(BaseModel):
    topic: str
    key_insights: List[str]
    hook_angle: str
    target_audience: str

class ResearchEngine:
    async def research_topic(self, topic: str) -> TopicResearchResult:
        """
        Gathers topic trends, background context, and hooks for short-form scripts.
        """
        return TopicResearchResult(
            topic=topic,
            key_insights=[f"Key insight 1 about {topic}", f"Key insight 2 about {topic}"],
            hook_angle=f"Did you know this mindblowing fact about {topic}?",
            target_audience="General audience interested in AI & technology"
        )
