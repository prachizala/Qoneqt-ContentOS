import os
import pytest
from ai.agents.researcher import ResearchAgent, ResearchResult
from ai.agents.scriptwriter import ScriptAgent, ScriptWriteResult
from ai.agents.scene_director import SceneDirector

@pytest.mark.asyncio
async def test_full_ai_pipeline_mock():
    """
    Tests the complete AI pipeline (Research -> Scriptwriter -> SceneDirector)
    using mock mode to verify Pydantic models, duration constraints, and Style Bible injection.
    """
    os.environ["USE_MOCK_AI"] = "true"

    topic = "Quantum Computing Breakthroughs in 2026"
    target_duration = 30

    # Step 1: Research Agent
    researcher = ResearchAgent()
    research: ResearchResult = await researcher.research_topic(
        topic=topic,
        audience="tech enthusiasts",
        objective="Explain complex quantum concepts simply",
        language="en"
    )

    assert isinstance(research, ResearchResult)
    assert research.core_concept != ""
    assert len(research.key_facts) >= 1
    assert len(research.hook_angles) >= 1
    assert research.suggested_cta != ""

    # Step 2: Scriptwriter Agent
    scriptwriter = ScriptAgent()
    script: ScriptWriteResult = await scriptwriter.write_script(
        research=research,
        duration=target_duration,
        style="cinematic"
    )

    assert isinstance(script, ScriptWriteResult)
    assert script.title != ""
    assert script.hook != ""
    assert script.cta != ""
    assert len(script.scenes) >= 1

    # Verify duration constraint (+/- 2 seconds)
    total_duration = sum(scene.duration for scene in script.scenes)
    assert abs(total_duration - target_duration) <= 2.0, (
        f"Total scene duration {total_duration}s deviates by more than 2s from target {target_duration}s"
    )

    # Step 3: Scene Director
    director = SceneDirector()
    directed_scenes = await director.direct_scenes(
        scenes=script.scenes,
        style="cinematic",
        aspect_ratio="9:16"
    )

    assert len(directed_scenes) == len(script.scenes)
    for scene in directed_scenes:
        assert "vertical 9:16 framing" in scene.visual_prompt
        assert "70% safe zone" in scene.visual_prompt
        assert "cinematic" in scene.visual_prompt

@pytest.mark.asyncio
async def test_tone_directives_selection():
    """
    Verifies that selecting different tone options (Informative, Storytelling, Satirical, Viral)
    produces distinct narrative hooks and scene vocabulary.
    """
    os.environ["USE_MOCK_AI"] = "true"
    researcher = ResearchAgent()
    research = await researcher.research_topic(topic="AI Agents in 2026")
    scriptwriter = ScriptAgent()

    tones = [
        "Viral / Hook Driven",
        "Informative & Educational",
        "Engaging Storytelling",
        "Satirical / Humorous"
    ]

    generated_hooks = set()
    for t in tones:
        res = await scriptwriter.write_script(research=research, duration=30, style="cinematic", tone=t)
        assert res.hook != ""
        generated_hooks.add(res.hook)
        assert len(res.scenes) >= 3

    # Ensure each tone produces unique hook angles
    assert len(generated_hooks) >= 3

@pytest.mark.asyncio
async def test_visual_style_isolation():
    """
    Verifies that selecting different Visual Style options applies strictly isolated style tokens
    without cross-pollination.
    """
    os.environ["USE_MOCK_AI"] = "true"
    researcher = ResearchAgent()
    research = await researcher.research_topic(topic="Future Robotics")
    scriptwriter = ScriptAgent()
    script = await scriptwriter.write_script(research=research, duration=30)
    director = SceneDirector()

    # 1. Cyberpunk Neon
    cyber_scenes = await director.direct_scenes(scenes=script.scenes, style="Cyberpunk Neon")
    for s in cyber_scenes:
        assert "neon color palette" in s.visual_prompt.lower()
        assert "octane render" not in s.visual_prompt.lower()
        assert "minimal shapes" not in s.visual_prompt.lower()

    # 2. Minimalist Modern
    mini_scenes = await director.direct_scenes(scenes=script.scenes, style="Minimalist Modern")
    for s in mini_scenes:
        assert "minimal shapes" in s.visual_prompt.lower()
        assert "neon color palette" not in s.visual_prompt.lower()
        assert "volumetric god rays" not in s.visual_prompt.lower()

    # 3. Photorealistic 3D
    photo_scenes = await director.direct_scenes(scenes=script.scenes, style="Photorealistic 3D")
    for s in photo_scenes:
        assert "octane render" in s.visual_prompt.lower()
        assert "neon color palette" not in s.visual_prompt.lower()
        assert "minimal shapes" not in s.visual_prompt.lower()

    # 4. Cinematic Volumetric
    cine_scenes = await director.direct_scenes(scenes=script.scenes, style="Cinematic Volumetric")
    for s in cine_scenes:
        assert "volumetric god rays" in s.visual_prompt.lower()
        assert "minimal shapes" not in s.visual_prompt.lower()
