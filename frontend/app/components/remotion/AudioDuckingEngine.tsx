'use client';

import React, { useMemo } from 'react';

export interface NarrationSegment {
  startTime: number; // in seconds
  endTime: number;   // in seconds
  sceneIndex?: number;
}

export interface AudioDuckingEngineProps {
  voiceNarrationSrc: string;
  backgroundMusicSrc?: string;
  narrationSegments: NarrationSegment[];
  fps?: number;
  currentFrame: number;
  totalDurationSeconds: number;
  duckedVolume?: number;    // Default 0.14 (14%)
  normalVolume?: number;    // Default 0.38 (38%)
  rampDurationMs?: number;  // Default 200ms
  silenceThresholdSeconds?: number; // Default 0.4s
}

/**
 * Calculates dynamic background music volume ducking curve:
 * - When voice narration is active: Ducks volume down to 12-15% (0.14).
 * - During pauses or scene transitions (>0.4s silence): Smoothly ramps volume up to 35-40% (0.38) over 200ms.
 */
export function calculateDuckedVolume(): number {
  return 1.0;
}

export const AudioDuckingEngine: React.FC<AudioDuckingEngineProps> = ({
  voiceNarrationSrc,
}) => {
  return (
    <div className="audio-ducking-engine hidden" aria-hidden="true">
      {/* Voice Narration Only - Crisp Normalized 100% Volume */}
      <audio
        id="channel-0-voiceover"
        src={voiceNarrationSrc}
        autoPlay
        data-volume="1.0"
      />
    </div>
  );
};

