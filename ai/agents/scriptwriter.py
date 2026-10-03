import logging
import re
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from ai.llm_client import LLMClient
from ai.agents.researcher import ResearchResult

logger = logging.getLogger(__name__)

TONE_DIRECTIVES: Dict[str, str] = {
    "viral": (
        "Viral / Hook Driven: High-energy pattern interruption, extreme curiosity gap, "
        "punchy fast-paced short sentences, cliffhangers, and urgent retention triggers."
    ),
    "informative": (
        "Informative & Educational: Clear pedagogical structure, fact-first breakdown, "
        "objective explanations, crisp step-by-step logic, and smooth didactic cadence."
    ),
    "storytelling": (
        "Engaging Storytelling: Compelling narrative arc (Hero/Conflict/Resolution), "
        "cinematic emotional pacing, vivid descriptive metaphors, and character immersion."
    ),
    "satirical": (
        "Satirical / Humorous: Witty, light-hearted irony, comedic hyperbole, "
        "playful skepticism, relatable banter, and punchline timing."
    )
}

def get_tone_directive(tone_input: Optional[str]) -> str:
    raw = (tone_input or "").lower()
    if "info" in raw or "edu" in raw:
        return TONE_DIRECTIVES["informative"]
    elif "story" in raw or "narrative" in raw:
        return TONE_DIRECTIVES["storytelling"]
    elif "satir" in raw or "humor" in raw or "funny" in raw:
        return TONE_DIRECTIVES["satirical"]
    else:
        return TONE_DIRECTIVES["viral"]

def clean_topic_prompt(topic: str) -> str:
    """Strips meta instructions (e.g. 'Explain how', 'Create a video about') from topic prompts."""
    cleaned = re.sub(r"^(explain how|create a video about|write a script about|show me how|tell me about)\s+", "", topic.strip(), flags=re.IGNORECASE)
    return cleaned.strip() or topic.strip()

class HookVariations(BaseModel):
    """
    3 distinct A/B hook variations for Scene 1 opening (0-4s).
    """
    hook_a: str = Field(description="Pattern Interrupt / Negative framing ('Stop doing X in 2026...')")
    hook_b: str = Field(description="Shocking Stat / Data-driven ('90% of engineers don't know...')")
    hook_c: str = Field(description="Curiosity Gap / Insider secret ('The dark truth about...')")

class ScriptScene(BaseModel):
    """
    Frame-by-frame scene definition for video rendering, motion synthesis, and narration.
    """
    scene_number: int = Field(description="1-indexed sequential scene number.")
    duration: float = Field(description="Scene duration in seconds (e.g., 4.5).")
    narration: str = Field(description="Voiceover narration text to be spoken by TTS.")
    visual_prompt: str = Field(description="Detailed prompt for clean AI image keyframe generation (no text/watermarks).")
    camera_direction: str = Field(default="Slow push-in shot, 9:16 vertical center focus", description="Cinematic camera motion directive.")
    kinetic_text: str = Field(default="KEY INSIGHT", description="Oversized kinetic typography keyword overlay.")
    motion_prompt: str = Field(default="Smooth camera pan across keyframe subject, 30fps fluid motion", description="Image-to-Video (I2V) motion prompt.")
    caption: str = Field(default="", description="On-screen subtitle text overlay.")
    transition: str = Field(default="fade", description="Transition effect into the next scene.")

class ScriptWriteResult(BaseModel):
    """
    Complete short-form video script payload containing timed storyboard scenes and A/B hook variations.
    """
    title: str = Field(description="Catchy video title.")
    hook: str = Field(description="Primary opening hook text.")
    hook_variations: HookVariations = Field(
        default_factory=lambda: HookVariations(
            hook_a="Stop scrolling! You need to see this right now.",
            hook_b="90% of people get this completely wrong.",
            hook_c="The insider secret nobody talks about."
        ),
        description="3 distinct opening hook variations for A/B testing: Hook A (Pattern Interrupt), Hook B (Shocking Stat), Hook C (Curiosity Gap)"
    )
    duration: int = Field(description="Target total video duration in seconds.")
    cta: str = Field(description="Call-to-action closing phrase.")
    scenes: List[ScriptScene] = Field(description="Sequential list of storyboard scenes.")

class ScriptAgent:
    """
    AI Scriptwriter Agent responsible for converting research into timed short-form video scenes.
    Dynamically maps tone directives and generates A/B hook variations.
    """
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    async def write_script(
        self,
        research: ResearchResult,
        duration: int = 30,
        style: str = "cinematic",
        tone: str = "Viral / Hook Driven"
    ) -> ScriptWriteResult:
        """
        Generates timed scene scripts strictly applying the requested Tone / Hook style and generating 3 A/B hook variations.
        """
        tone_directive = get_tone_directive(tone)
        logger.info(f"[ScriptAgent] Generating {duration}s script in '{style}' style with tone: '{tone}'...")

        clean_concept = clean_topic_prompt(research.core_concept)

        # Calculate word budget and scene count based on target duration
        target_scene_count = max(3, min(8, round(duration / 5.0)))
        max_total_words = int(duration * 2.2) # ~2.2 words per second speaking speed
        max_words_per_scene = max(5, int(max_total_words / target_scene_count))

        system_prompt = (
            "You are a Master Short-Form Video Director for TikTok, Reels, and Qoneqt. "
            f"Target Tone and Pacing: {tone_directive}. Script each scene's narration strictly adhering to this tone. "
            f"Write a high-retention 9:16 vertical short video script structured into exactly {target_scene_count} scenes. "
            f"Target total duration is {duration} seconds. "
            f"CRITICAL CONSTRAINT: Total narration across ALL scenes MUST NOT exceed {max_total_words} words "
            f"(approx {max_words_per_scene} words per scene) so voiceover narration fits strictly within {duration} seconds when spoken.\n"
            "CRITICAL A/B HOOK REQUIREMENT: Generate 3 distinct Hook variations for Scene 1 (0-4 seconds):\n"
            "  - hook_a: Pattern Interrupt / Negative framing (e.g. 'Stop doing X in 2026...')\n"
            "  - hook_b: Shocking Stat / Data-driven (e.g. '90% of engineers don't know...')\n"
            "  - hook_c: Curiosity Gap / Insider secret (e.g. 'The dark truth about...')\n"
            "Ensure scenes include: concise narration, clean visual prompts (without text), camera directions, "
            "kinetic headline words, and image-to-video motion prompts."
        )

        user_prompt = (
            f"Core Concept: {clean_concept}\n"
            f"Key Facts:\n" + "\n".join(f"- {fact}" for fact in research.key_facts) + "\n"
            f"Suggested CTA: {research.suggested_cta}\n"
            f"Visual Style: {style}\n"
            f"Tone / Hook Style: {tone}\n"
            f"Target Duration: {duration} seconds ({target_scene_count} scenes, max {max_total_words} words total)\n\n"
            f"Generate {target_scene_count} scenes with 3 distinct hook_variations (hook_a, hook_b, hook_c), visual_prompt, camera_direction, kinetic_text, motion_prompt, and caption."
        )

        mock_fallback = self._generate_mock_script(research, duration, style, tone)

        result = await self.llm_client.generate_structured(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=ScriptWriteResult,
            mock_fallback=mock_fallback
        )

        return self._normalize_scene_durations(result, duration)

    def _normalize_scene_durations(self, result: ScriptWriteResult, target_duration: int) -> ScriptWriteResult:
        """
        Normalizes scene durations so their sum is strictly equal to target_duration.
        """
        if not result.scenes:
            return result

        total_actual = sum(s.duration for s in result.scenes)

        if total_actual > 0:
            logger.info(f"[ScriptAgent] Adjusting scene durations from sum={total_actual:.1f}s to target={target_duration}s")
            scale_factor = target_duration / total_actual
            for scene in result.scenes:
                scene.duration = round(scene.duration * scale_factor, 1)

            new_total = sum(s.duration for s in result.scenes)
            diff = round(target_duration - new_total, 1)
            if diff != 0:
                result.scenes[-1].duration = round(result.scenes[-1].duration + diff, 1)

            result.duration = target_duration

        return result

    def _generate_mock_script(self, research: ResearchResult, target_duration: int, style: str, tone: str = "Viral / Hook Driven") -> ScriptWriteResult:
        """
        Provides realistic mock script data customized by tone, style, duration, and 3 A/B hooks.
        """
        clean_concept = clean_topic_prompt(research.core_concept)
        raw_tone = (tone or "").lower()

        scene_count = 3 if target_duration <= 20 else 5
        base_dur = round(target_duration / scene_count, 1)

        # 3 A/B Hook variations customized to the topic
        hook_a = f"Stop ignoring {clean_concept} in 2026 or get left behind."
        hook_b = f"90% of leaders have no idea how {clean_concept} actually works."
        hook_c = f"The hidden truth about {clean_concept} that experts won't tell you."
        hook_variations = HookVariations(hook_a=hook_a, hook_b=hook_b, hook_c=hook_c)

        # 1. Informative & Educational tone
        if "info" in raw_tone or "edu" in raw_tone:
            hook = f"Here is what you need to know about {clean_concept}."
            scenes = [
                ScriptScene(
                    scene_number=1,
                    duration=base_dur,
                    narration=f"Let's break down the technical architecture of {clean_concept}.",
                    visual_prompt=f"Detailed blueprint diagram illustrating {clean_concept}, clean technical lighting, {style}, 9:16 vertical",
                    camera_direction="Slow push-in shot, 9:16 vertical center focus",
                    kinetic_text="TECHNICAL BREAKDOWN",
                    motion_prompt="Smooth analytical camera pan over digital architectural schematic",
                    caption=f"Understanding {clean_concept}",
                    transition="fade"
                ),
                ScriptScene(
                    scene_number=2,
                    duration=base_dur,
                    narration=research.key_facts[0] if research.key_facts else f"First, research proves that {clean_concept} delivers measurable efficiency.",
                    visual_prompt=f"High-precision data analytics dashboard showing performance metrics, {style}",
                    camera_direction="Smooth horizontal pan across data graphs",
                    kinetic_text="FACT #1: PROVEN DATA",
                    motion_prompt="Glowing data bars updating smoothly in real-time",
                    caption="Fact #1: Key Metric",
                    transition="crossfade"
                ),
                ScriptScene(
                    scene_number=3,
                    duration=base_dur,
                    narration=research.key_facts[1] if len(research.key_facts) > 1 else f"Second, industry standards are adapting worldwide.",
                    visual_prompt=f"Modern laboratory server matrix processing data streams, {style}",
                    camera_direction="Steady vertical tilt up server column",
                    kinetic_text="FACT #2: ADOPTION",
                    motion_prompt="Clean server light indicators pulsing systematically",
                    caption="Fact #2: Global Impact",
                    transition="fade"
                ),
            ]
            if scene_count == 5:
                scenes.extend([
                    ScriptScene(
                        scene_number=4,
                        duration=base_dur,
                        narration="In summary, mastering these core principles provides an immediate strategic advantage.",
                        visual_prompt=f"Futuristic knowledge hub with holographic data charts, {style}",
                        camera_direction="Cinematic aerial drift over knowledge matrix",
                        kinetic_text="CORE SUMMARY",
                        motion_prompt="Hologram charts rotating slowly in 3D space",
                        caption="Summary & Takeaway",
                        transition="fade"
                    ),
                    ScriptScene(
                        scene_number=5,
                        duration=base_dur,
                        narration=research.suggested_cta,
                        visual_prompt=f"Clean minimalist dark technology background with glowing teal energy lines, {style}",
                        camera_direction="Static hero shot with subtle ambient lighting pulse",
                        kinetic_text="QONEQT AI",
                        motion_prompt="Ambient teal neon waves pulsing gently across dark metallic background",
                        caption=research.suggested_cta,
                        transition="fade"
                    )
                ])
            else:
                scenes[-1].narration = research.suggested_cta

            return ScriptWriteResult(
                title=f"The Science of {clean_concept}",
                hook=hook,
                hook_variations=hook_variations,
                duration=target_duration,
                cta=research.suggested_cta,
                scenes=scenes
            )

        # 2. Engaging Storytelling tone
        elif "story" in raw_tone or "narrative" in raw_tone:
            hook = f"Imagine waking up to a world where {clean_concept} changed everything."
            scenes = [
                ScriptScene(
                    scene_number=1,
                    duration=base_dur,
                    narration=f"It started quietly, but {clean_concept} was about to transform our entire reality.",
                    visual_prompt=f"Cinematic hero walking through a mysterious glowing futuristic city at twilight, {style}",
                    camera_direction="Cinematic orbit shot with shallow depth of field",
                    kinetic_text="THE AWAKENING",
                    motion_prompt="Moody atmospheric fog rolling through cyberpunk city streets as camera tracks forward",
                    caption="The Journey Begins",
                    transition="crossfade"
                ),
                ScriptScene(
                    scene_number=2,
                    duration=base_dur,
                    narration=f"Engineers and creators faced a massive challenge, until this breakthrough emerged.",
                    visual_prompt=f"Hero scientist collaborating before an illuminated quantum terminal, {style}",
                    camera_direction="Dynamic tracking shot across subject",
                    kinetic_text="THE TURNING POINT",
                    motion_prompt="Dramatic light flare sweeping across the scientist's focused face",
                    caption="The Turning Point",
                    transition="fade"
                ),
                ScriptScene(
                    scene_number=3,
                    duration=base_dur,
                    narration=research.key_facts[0] if research.key_facts else f"Now, the impossible has become the new benchmark.",
                    visual_prompt=f"Vast futuristic horizon glowing with golden sunrise and digital energy beams, {style}",
                    camera_direction="Smooth vertical tilt up into morning sky",
                    kinetic_text="THE RESOLUTION",
                    motion_prompt="Golden light rays bursting through clouds illuminating a new metropolis",
                    caption="The New Horizon",
                    transition="fade"
                ),
            ]
            if scene_count == 5:
                scenes.extend([
                    ScriptScene(
                        scene_number=4,
                        duration=base_dur,
                        narration="And this is only the first chapter of what comes next.",
                        visual_prompt=f"Epic portal opening into boundless digital stars, {style}",
                        camera_direction="Fast zoom-in towards glowing dimensional doorway",
                        kinetic_text="THE FUTURE",
                        motion_prompt="Swirling stellar vortex pulling camera into infinite cyberspace",
                        caption="A New Chapter",
                        transition="zoom_in"
                    ),
                    ScriptScene(
                        scene_number=5,
                        duration=base_dur,
                        narration=research.suggested_cta,
                        visual_prompt=f"Clean minimalist dark technology background with glowing teal energy lines, {style}",
                        camera_direction="Static hero shot with subtle ambient lighting pulse",
                        kinetic_text="QONEQT AI",
                        motion_prompt="Ambient teal neon waves pulsing gently across dark metallic background",
                        caption=research.suggested_cta,
                        transition="fade"
                    )
                ])
            else:
                scenes[-1].narration = research.suggested_cta

            return ScriptWriteResult(
                title=f"The Story of {clean_concept}",
                hook=hook,
                hook_variations=hook_variations,
                duration=target_duration,
                cta=research.suggested_cta,
                scenes=scenes
            )

        # 3. Satirical / Humorous tone
        elif "satir" in raw_tone or "humor" in raw_tone or "funny" in raw_tone:
            hook = f"You won't believe how everyone completely misunderstood {clean_concept}."
            scenes = [
                ScriptScene(
                    scene_number=1,
                    duration=base_dur,
                    narration=f"Spoiler alert: Everything you thought you knew about {clean_concept} is hilarious.",
                    visual_prompt=f"Comical dramatic robot wearing oversized glasses analyzing charts, {style}",
                    camera_direction="Snap zoom into expressive robot eyes",
                    kinetic_text="SPOILER ALERT",
                    motion_prompt="Robot tilting head comically with blinking neon eyes",
                    caption="Spoiler Alert!",
                    transition="zoom_in"
                ),
                ScriptScene(
                    scene_number=2,
                    duration=base_dur,
                    narration=f"While everyone panicked, the machines were just following simple logic.",
                    visual_prompt=f"Futuristic office where cute AI drones serve coffee to confused executives, {style}",
                    camera_direction="Smooth horizontal pan across bewildered boardroom",
                    kinetic_text="THE REALITY",
                    motion_prompt="Drones hovering playfully while executives stare in disbelief",
                    caption="Expectation vs Reality",
                    transition="crossfade"
                ),
                ScriptScene(
                    scene_number=3,
                    duration=base_dur,
                    narration=research.key_facts[0] if research.key_facts else "Turns out, working smarter actually works!",
                    visual_prompt=f"Glowing celebration confetti in a sleek cyberpunk lounge, {style}",
                    camera_direction="Dynamic tracking shot across laughing cyborg characters",
                    kinetic_text="PUNCHLINE",
                    motion_prompt="Neon confetti falling in slow motion over futuristic party",
                    caption="Work Smarter",
                    transition="fade"
                ),
            ]
            if scene_count == 5:
                scenes.extend([
                    ScriptScene(
                        scene_number=4,
                        duration=base_dur,
                        narration="So don't panic, just sit back and let the algorithms do the heavy lifting.",
                        visual_prompt=f"Futuristic hammock suspended between floating servers in space, {style}",
                        camera_direction="Cinematic aerial drift over cosmic hammock",
                        kinetic_text="CHILL OUT",
                        motion_prompt="Hammock swinging gently against backdrop of colorful nebulas",
                        caption="Sit Back & Relax",
                        transition="fade"
                    ),
                    ScriptScene(
                        scene_number=5,
                        duration=base_dur,
                        narration=research.suggested_cta,
                        visual_prompt=f"Clean minimalist dark technology background with glowing teal energy lines, {style}",
                        camera_direction="Static hero shot with subtle ambient lighting pulse",
                        kinetic_text="QONEQT AI",
                        motion_prompt="Ambient teal neon waves pulsing gently across dark metallic background",
                        caption=research.suggested_cta,
                        transition="fade"
                    )
                ])
            else:
                scenes[-1].narration = research.suggested_cta

            return ScriptWriteResult(
                title=f"The Funny Truth About {clean_concept}",
                hook=hook,
                hook_variations=hook_variations,
                duration=target_duration,
                cta=research.suggested_cta,
                scenes=scenes
            )

        # 4. Default: Viral / Hook Driven tone
        else:
            hook = research.hook_angles[0] if research.hook_angles else f"Stop scrolling! This changes everything about {clean_concept}."
            scenes = [
                ScriptScene(
                    scene_number=1,
                    duration=base_dur,
                    narration=f"Stop scrolling! AI is completely rewiring {clean_concept} in 2026.",
                    visual_prompt=f"Futuristic command center with glowing digital threat matrix, {style} lighting, 9:16 vertical wallpaper",
                    camera_direction="Fast zoom-in to glowing holographic core",
                    kinetic_text="STOP SCROLLING",
                    motion_prompt="Cyberpunk holographic server matrix pulsing with red threat vectors, smooth camera drift",
                    caption=f"{clean_concept} in 2026",
                    transition="zoom_in"
                ),
                ScriptScene(
                    scene_number=2,
                    duration=base_dur,
                    narration=research.key_facts[0] if research.key_facts else f"Autonomous neural networks are executing tasks in milliseconds.",
                    visual_prompt=f"Glowing blue neural network shield deflecting digital laser attacks, {style}",
                    camera_direction="Dynamic tracking shot across shield boundary",
                    kinetic_text="DEFENSE MATRIX",
                    motion_prompt="Glowing pulse wave deflecting incoming digital light streams, high speed dynamic camera move",
                    caption="Fact #1: Millisecond Defense",
                    transition="crossfade"
                ),
                ScriptScene(
                    scene_number=3,
                    duration=base_dur,
                    narration=research.key_facts[1] if len(research.key_facts) > 1 else f"Quantum algorithms are protecting critical systems worldwide.",
                    visual_prompt=f"High-tech server room with quantum crystal processing cores and neon blue fiber optics, {style}",
                    camera_direction="Smooth vertical tilt up glowing server tower",
                    kinetic_text="QUANTUM SHIELD",
                    motion_prompt="Quantum particles swirling around crystal server pillar, 30fps fluid camera elevation",
                    caption="Fact #2: Quantum Shield",
                    transition="fade"
                ),
            ]
            if scene_count == 5:
                scenes.extend([
                    ScriptScene(
                        scene_number=4,
                        duration=base_dur,
                        narration="Organizations taking advantage of this report 90 percent higher efficiency.",
                        visual_prompt=f"Futuristic cityscape at night with glowing green security grid overhead, {style}",
                        camera_direction="Cinematic aerial drift over futuristic metropolis",
                        kinetic_text="90% ADVANTAGE",
                        motion_prompt="Smooth drone flyover glowing digital grid expanding across city skyline",
                        caption="90% Improvement",
                        transition="fade"
                    ),
                    ScriptScene(
                        scene_number=5,
                        duration=base_dur,
                        narration=research.suggested_cta,
                        visual_prompt=f"Clean minimalist dark technology background with glowing teal energy lines, {style}",
                        camera_direction="Static hero shot with subtle ambient lighting pulse",
                        kinetic_text="QONEQT AI",
                        motion_prompt="Ambient teal neon waves pulsing gently across dark metallic background",
                        caption=research.suggested_cta,
                        transition="fade"
                    )
                ])
            else:
                scenes[-1].narration = research.suggested_cta

            return ScriptWriteResult(
                title=f"{clean_concept} Breakdown",
                hook=hook,
                hook_variations=hook_variations,
                duration=target_duration,
                cta=research.suggested_cta,
                scenes=scenes
            )
