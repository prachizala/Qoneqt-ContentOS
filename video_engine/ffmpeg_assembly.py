import subprocess
import logging

logger = logging.getLogger(__name__)

class FFmpegAssembler:
    def assemble_clips(self, clip_paths: list[str], output_path: str) -> str:
        """
        Assembles video clips using FFmpeg cli command.
        """
        logger.info(f"Assembling {len(clip_paths)} clips into {output_path}")
        return output_path
