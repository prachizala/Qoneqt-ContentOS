import re
import logging
from typing import List, Dict, Optional
from ai.agents.scriptwriter import ScriptScene

logger = logging.getLogger(__name__)

STYLE_BIBLES: Dict[str, str] = {
    "cinematic": (
        "cinematic lighting, volumetric god rays, anamorphic lens flare, "
        "shallow depth of field, 35mm film grain, 8k resolution, highly detailed, photorealistic render"
    ),
    "photorealistic": (
        "octane render, unreal engine 5 render, raytracing, global illumination, "
        "hyper-realistic textures, clean architectural studio lighting, 8k"
    ),
    "cyberpunk": (
        "neon color palette (vibrant cyan, hot pink, deep purple), futuristic dystopian aesthetic, "
        "reflective wet pavement, high contrast, dark atmospheric lighting"
    ),
    "minimalist": (
        "clean composition, minimal shapes, sleek negative space, "
        "soft ambient studio lighting, elegant color harmony, uncluttered background, premium editorial look"
    )
}

def get_style_tokens(style_input: Optional[str]) -> str:
    """
    Returns isolated, mutually exclusive style bible tokens for the chosen style.
    Guarantees no keyword cross-pollination.
    """
    raw = (style_input or "").lower()
    if "photo" in raw or "3d" in raw:
        return STYLE_BIBLES["photorealistic"]
    elif "cyber" in raw or "neon" in raw:
        return STYLE_BIBLES["cyberpunk"]
    elif "minim" in raw or "modern" in raw:
        return STYLE_BIBLES["minimalist"]
    else:
        return STYLE_BIBLES["cinematic"]

class SceneDirector:
    """
    AI Scene Director Agent responsible for injecting isolated style bible directives,
    mobile 9:16 safe-zone framing constraints, camera movements, and motion prompts into scene plans.
    """
    def __init__(self, style_preset: str = "Cinematic Volumetric"):
        self.style_preset = style_preset

    async def direct_scenes(
        self,
        scenes: List[ScriptScene],
        style: str = "Cinematic Volumetric",
        aspect_ratio: str = "9:16",
        tone: str = "Viral / Hook Driven"
    ) -> List[ScriptScene]:
        """
        Enhances scene visual & motion prompts with strict style isolation, camera directions,
        safe-zone framing, no-text AI generation rules, and kinetic typography highlights.
        """
        selected_style_tokens = get_style_tokens(style)
        logger.info(f"[SceneDirector] Directing {len(scenes)} scenes with style: '{style}' and tone: '{tone}'.")

        raw_tone = (tone or "").lower()
        if "story" in raw_tone:
            camera_movements = [
                "Cinematic orbit shot with shallow depth of field",
                "Moody tracking shot across hero subject",
                "Smooth vertical pan into golden horizon",
                "Fast zoom-in towards glowing dimensional doorway",
                "Static hero shot with subtle ambient lighting pulse"
            ]
        elif "satir" in raw_tone or "humor" in raw_tone:
            camera_movements = [
                "Snap zoom into comical subject",
                "Smooth horizontal pan across bewildered room",
                "Dynamic tracking shot across laughing characters",
                "Cinematic aerial drift over scene",
                "Static hero shot with ambient lighting pulse"
            ]
        elif "info" in raw_tone or "edu" in raw_tone:
            camera_movements = [
                "Slow push-in shot, 9:16 vertical center focus",
                "Smooth horizontal pan across data analytics",
                "Steady vertical tilt up technical matrix",
                "Cinematic aerial drift over knowledge hub",
                "Static hero shot with subtle ambient lighting pulse"
            ]
        else:
            camera_movements = [
                "Fast zoom-in to glowing core",
                "Dynamic tracking shot across shield boundary",
                "Smooth vertical tilt up glowing tower",
                "Smooth drone flyover glowing digital grid",
                "Static hero shot with ambient lighting pulse"
            ]

        directed_scenes: List[ScriptScene] = []

        for idx, scene in enumerate(scenes):
            camera_tag = scene.camera_direction or camera_movements[idx % len(camera_movements)]
            
            # 1. Clean and isolate visual concept from any baked-in tokens
            clean_concept = re.sub(r"\[.*?\]", "", scene.visual_prompt).strip()
            clean_concept = re.sub(r",?\s*(style:|cinematic|photorealistic|cyberpunk|minimalist|8k|lighting).*$", "", clean_concept, flags=re.IGNORECASE).strip(" ,.")

            # 2. Strict style injection without token cross-pollination
            no_text_directive = "no text, no watermarks, no baked-in captions, clean frame"
            safe_zone_directive = "vertical 9:16 framing, center 70% safe zone for mobile feeds"
            
            enhanced_visual = f"{clean_concept}, style: {selected_style_tokens}, {safe_zone_directive}, {camera_tag}, {no_text_directive}"
            enhanced_motion = f"{scene.motion_prompt or camera_tag}, 30fps fluid camera motion, 9:16 vertical stream"

            # 3. Derive kinetic keyword text if missing
            kinetic_word = scene.kinetic_text
            if not kinetic_word or kinetic_word == "KEY INSIGHT":
                words = [w.upper() for w in (scene.caption or scene.narration).split() if len(w) >= 4]
                kinetic_word = " ".join(words[:2]) if words else "QONEQT AI"

            directed_scene = ScriptScene(
                scene_number=scene.scene_number,
                duration=scene.duration,
                narration=scene.narration,
                visual_prompt=enhanced_visual,
                camera_direction=camera_tag,
                kinetic_text=kinetic_word,
                motion_prompt=enhanced_motion,
                caption=scene.caption or scene.narration,
                transition=scene.transition or "fade"
            )
            directed_scenes.append(directed_scene)

        return directed_scenes
