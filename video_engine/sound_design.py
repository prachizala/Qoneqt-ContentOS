import os
import math
import struct
import wave
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SoundDesignEngine:
    """
    Automated Sound Design & Procedural SFX Engine for Qoneqt Video Pipeline.
    Calculates trigger timestamps for scene transitions and kinetic text punch-in reveals,
    and generates balanced procedural sound effects (whoosh/swoosh/punch) at 30-40% volume relative to narration.
    """
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate

    def generate_procedural_whoosh(
        self,
        output_path: str,
        duration: float = 0.35,
        start_freq: float = 120.0,
        peak_freq: float = 1200.0,
        end_freq: float = 180.0,
        peak_volume: float = 0.35
    ) -> str:
        """
        Synthesizes a procedural aerodynamic whoosh/swoosh SFX using swept sine-filtered noise & envelope.
        Generates a clean 16-bit PCM WAV file without requiring external audio asset dependencies.
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        total_samples = int(self.sample_rate * duration)
        num_channels = 1
        bytes_per_sample = 2  # 16-bit PCM
        max_amplitude = 32767.0 * peak_volume

        try:
            import numpy as np
            # High-fidelity synthesis using numpy
            t = np.linspace(0, duration, total_samples, endpoint=False)
            
            # Smooth bell-shaped volume envelope (hanning/cosine window)
            envelope = np.sin(np.pi * (t / duration)) ** 2
            
            # Frequency sweep trajectory (exponential rise then exponential fall)
            mid_idx = total_samples // 2
            freq_curve = np.zeros(total_samples)
            freq_curve[:mid_idx] = np.geomspace(start_freq, peak_freq, mid_idx)
            freq_curve[mid_idx:] = np.geomspace(peak_freq, end_freq, total_samples - mid_idx)
            
            # Phase accumulation for instantaneous frequency
            phase = 2 * np.pi * np.cumsum(freq_curve) / self.sample_rate
            
            # Hybrid synth: Swept sine + filtered white noise component
            noise = np.random.uniform(-0.4, 0.4, total_samples)
            synth_wave = (0.7 * np.sin(phase) + 0.3 * noise) * envelope
            
            # Soft clipping / normalization
            synth_wave = np.clip(synth_wave, -1.0, 1.0)
            audio_data = (synth_wave * max_amplitude).astype(np.int16).tobytes()

        except Exception:
            # Fallback pure-python wave synthesis if numpy unavailable
            audio_bytes = bytearray()
            for i in range(total_samples):
                t_val = i / self.sample_rate
                rel_t = t_val / duration
                
                # Bell envelope
                envelope = math.sin(math.pi * rel_t) ** 2
                
                # Frequency sweep
                if rel_t < 0.5:
                    freq = start_freq + (peak_freq - start_freq) * (rel_t * 2)
                else:
                    freq = peak_freq - (peak_freq - end_freq) * ((rel_t - 0.5) * 2)
                
                phase = 2 * math.pi * freq * t_val
                # Pseudo-noise modulation
                noise = ((i * 1103515245 + 12345) & 0x7FFFFFFF) / 0x7FFFFFFF - 0.5
                sample_val = (0.75 * math.sin(phase) + 0.25 * noise) * envelope * max_amplitude
                sample_int = max(-32768, min(32767, int(sample_val)))
                audio_bytes.extend(struct.pack("<h", sample_int))
            audio_data = bytes(audio_bytes)

        with wave.open(output_path, "wb") as wav_file:
            wav_file.setnchannels(num_channels)
            wav_file.setsampwidth(bytes_per_sample)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data)

        return output_path

    def generate_procedural_punch(
        self,
        output_path: str,
        duration: float = 0.18,
        freq: float = 240.0,
        peak_volume: float = 0.30
    ) -> str:
        """
        Synthesizes a subtle, punchy kinetic text-reveal transient SFX (short pop/drop).
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        total_samples = int(self.sample_rate * duration)
        num_channels = 1
        bytes_per_sample = 2
        max_amplitude = 32767.0 * peak_volume

        try:
            import numpy as np
            t = np.linspace(0, duration, total_samples, endpoint=False)
            decay = np.exp(-t * 25.0)  # Fast percussive decay
            # Pitch drop envelope (frequency drops rapidly)
            pitch_envelope = freq * (1.0 + 2.5 * np.exp(-t * 40.0))
            phase = 2 * np.pi * np.cumsum(pitch_envelope) / self.sample_rate
            synth_wave = np.sin(phase) * decay
            synth_wave = np.clip(synth_wave, -1.0, 1.0)
            audio_data = (synth_wave * max_amplitude).astype(np.int16).tobytes()
        except Exception:
            audio_bytes = bytearray()
            for i in range(total_samples):
                t_val = i / self.sample_rate
                decay = math.exp(-t_val * 25.0)
                pitch = freq * (1.0 + 2.5 * math.exp(-t_val * 40.0))
                phase = 2 * math.pi * pitch * t_val
                sample_val = math.sin(phase) * decay * max_amplitude
                sample_int = max(-32768, min(32767, int(sample_val)))
                audio_bytes.extend(struct.pack("<h", sample_int))
            audio_data = bytes(audio_bytes)

        with wave.open(output_path, "wb") as wav_file:
            wav_file.setnchannels(num_channels)
            wav_file.setsampwidth(bytes_per_sample)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data)

        return output_path

    def calculate_sfx_trigger_events(
        self,
        scene_assets: List[Dict[str, Any]],
        subtitle_timings: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Reverted trigger event calculation (procedural SFX disabled).
        """
        return []

    def render_composite_sfx_track(
        self,
        sfx_events: List[Dict[str, Any]],
        total_duration: float,
        output_track_path: str,
        work_dir: str
    ) -> str:
        """
        Generates a silent fallback track matching total_duration.
        """
        Path(output_track_path).parent.mkdir(parents=True, exist_ok=True)
        total_samples = int(self.sample_rate * (total_duration + 0.5))
        int_data = bytearray(total_samples * 2)

        with wave.open(output_track_path, "wb") as out_wav:
            out_wav.setnchannels(1)
            out_wav.setsampwidth(2)
            out_wav.setframerate(self.sample_rate)
            out_wav.writeframes(int_data)

        return output_track_path
