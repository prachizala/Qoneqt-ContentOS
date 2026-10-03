'use client';

import React, { useMemo } from 'react';
import { getEmojiForWord } from './emojiMatcher';

export type CaptionPreset = 'Bouncy Pop-in' | 'Smooth Slide-up' | 'Word-Reveal';
export type HighlightColor = 'yellow' | 'neon-green' | 'cyan';

export interface WordTimestamp {
  word: string;
  start: number; // in seconds
  end: number;   // in seconds
}

export interface ViralCaptionsProps {
  words: WordTimestamp[];
  currentTime: number; // in seconds
  preset?: CaptionPreset;
  highlightColor?: HighlightColor;
  chunkSize?: number; // 2 to 4 words per view
  className?: string;
}

export const ViralCaptions: React.FC<ViralCaptionsProps> = ({
  words,
  currentTime,
  preset = 'Bouncy Pop-in',
  highlightColor = 'yellow',
  chunkSize = 3,
  className = '',
}) => {
  // Partition word timestamps into chunks of 2-4 words
  const chunks = useMemo(() => {
    if (!words || words.length === 0) return [];
    const res: WordTimestamp[][] = [];
    const size = Math.max(2, Math.min(4, chunkSize));
    for (let i = 0; i < words.length; i += size) {
      res.push(words.slice(i, i + size));
    }
    return res;
  }, [words, chunkSize]);

  // Find active chunk for current playback time
  const activeChunk = useMemo(() => {
    if (chunks.length === 0) return null;
    
    // Check if within any chunk timeframe
    for (const chunk of chunks) {
      const chunkStart = chunk[0].start;
      const chunkEnd = chunk[chunk.length - 1].end;
      if (currentTime >= chunkStart && currentTime <= chunkEnd + 0.25) {
        return chunk;
      }
    }

    // Default to chunk closest to currentTime
    let closest = chunks[0];
    let minDiff = Infinity;
    for (const chunk of chunks) {
      const chunkMid = (chunk[0].start + chunk[chunk.length - 1].end) / 2;
      const diff = Math.abs(currentTime - chunkMid);
      if (diff < minDiff) {
        minDiff = diff;
        closest = chunk;
      }
    }
    return closest;
  }, [chunks, currentTime]);

  if (!activeChunk || activeChunk.length === 0) {
    return null;
  }

  const highlightStyles = {
    yellow: {
      activeText: 'text-[#FFE600]',
      glow: 'drop-shadow-[0_0_16px_rgba(255,230,0,0.85)]',
      bgTag: 'bg-[#FFE600]/20 border-[#FFE600]/50',
    },
    'neon-green': {
      activeText: 'text-[#00FF66]',
      glow: 'drop-shadow-[0_0_16px_rgba(0,255,102,0.85)]',
      bgTag: 'bg-[#00FF66]/20 border-[#00FF66]/50',
    },
    cyan: {
      activeText: 'text-[#00F0FF]',
      glow: 'drop-shadow-[0_0_16px_rgba(0,240,255,0.85)]',
      bgTag: 'bg-[#00F0FF]/20 border-[#00F0FF]/50',
    }
  }[highlightColor];

  return (
    <div
      className={`viral-captions-container flex flex-col items-center justify-center pointer-events-none select-none ${className}`}
    >
      <div className="flex flex-wrap items-center justify-center gap-x-2 gap-y-2 px-4 py-2 bg-black/60 backdrop-blur-md rounded-2xl border border-white/10 shadow-2xl">
        {activeChunk.map((item, idx) => {
          const isActive = currentTime >= item.start && currentTime <= item.end;
          const isPassed = currentTime > item.end;
          const emoji = getEmojiForWord(item.word);

          // Animation preset styling
          let animationClass = '';
          if (preset === 'Bouncy Pop-in') {
            animationClass = isActive
              ? 'scale-110 -translate-y-1 transition-all duration-150 ease-out animate-pulse'
              : 'scale-100 translate-y-0 transition-all duration-200';
          } else if (preset === 'Smooth Slide-up') {
            animationClass = isActive
              ? 'translate-y-0 opacity-100 transition-all duration-200 ease-out'
              : isPassed
              ? 'translate-y-0 opacity-80'
              : 'translate-y-2 opacity-50';
          } else if (preset === 'Word-Reveal') {
            animationClass = isActive || isPassed
              ? 'opacity-100 scale-105 transition-opacity duration-100'
              : 'opacity-30 scale-95';
          }

          return (
            <div
              key={`${item.word}-${idx}-${item.start}`}
              className={`relative inline-flex flex-col items-center justify-center ${animationClass}`}
            >
              {/* Contextual Emoji floating above highlighted active word */}
              {emoji && isActive && (
                <span className="absolute -top-7 text-2xl animate-bounce drop-shadow-md z-30 select-none">
                  {emoji}
                </span>
              )}

              {/* Spoken Word Item */}
              <span
                className={`font-black uppercase tracking-tight text-xl md:text-2xl px-1.5 py-0.5 rounded-lg transition-colors ${
                  isActive
                    ? `${highlightStyles.activeText} ${highlightStyles.glow} ${highlightStyles.bgTag} font-extrabold`
                    : 'text-white drop-shadow-[0_2px_4px_rgba(0,0,0,0.9)] opacity-90'
                }`}
                style={{
                  textShadow: isActive
                    ? '0 0 12px currentColor, 0 3px 6px rgba(0,0,0,0.9)'
                    : '0 2px 4px rgba(0,0,0,0.95), 0 0 2px rgba(0,0,0,0.8)',
                  WebkitTextStroke: isActive ? '1px rgba(0,0,0,0.4)' : '0.5px rgba(0,0,0,0.7)',
                }}
              >
                {item.word}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
