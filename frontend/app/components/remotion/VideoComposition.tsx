'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { Play, Pause, Volume2, Sparkles, Wand2, Palette, Flame, Monitor, Smartphone, Square } from 'lucide-react';
import {
  AudioDuckingEngine,
  calculateDuckedVolume,
  NarrationSegment
} from './AudioDuckingEngine';
import {
  SFXTriggerEngine,
  generateSFXTimeline,
  SFXEvent
} from './SFXTriggerEngine';
import {
  ViralCaptions,
  CaptionPreset,
  HighlightColor,
  WordTimestamp
} from './ViralCaptions';

export type AspectRatioProfile = '9:16' | '16:9' | '1:1';

export interface SceneData {
  id: string;
  image_url: string;
  duration: number;
  narration: string;
  caption?: string;
  kinetic_text?: string;
  word_timings?: Array<{ word: string; start: number; end: number }>;
}

export interface VideoCompositionProps {
  scenes: SceneData[];
  voiceoverUrl: string;
  aspectRatio?: AspectRatioProfile;
  initialPreset?: CaptionPreset;
  initialHighlightColor?: HighlightColor;
}

export const VideoComposition: React.FC<VideoCompositionProps> = ({
  scenes,
  voiceoverUrl,
  aspectRatio: defaultRatio = '9:16',
  initialPreset = 'Bouncy Pop-in',
  initialHighlightColor = 'yellow'
}) => {
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const [currentRatio, setCurrentRatio] = useState<AspectRatioProfile>(defaultRatio);
  const [captionPreset, setCaptionPreset] = useState<CaptionPreset>(initialPreset);
  const [highlightColor, setHighlightColor] = useState<HighlightColor>(initialHighlightColor);

  const totalDuration = scenes.reduce((acc, s) => acc + (s.duration || 3.5), 0);

  // Build narration segments from scenes
  const narrationSegments: NarrationSegment[] = useMemo(() => {
    let t = 0;
    return scenes.map((sc, idx) => {
      const start = t;
      const speechDur = Math.max(1.0, (sc.duration || 3.5) - 0.4);
      const end = start + speechDur;
      t += sc.duration || 3.5;
      return { startTime: start, endTime: end, sceneIndex: idx };
    });
  }, [scenes]);

  // Compute SFX timeline events
  const sfxEvents: SFXEvent[] = useMemo(() => {
    return generateSFXTimeline(scenes, 0.35, 0.30);
  }, [scenes]);

  // Flatten all word timestamps with absolute timeline offsets
  const allWordTimestamps: WordTimestamp[] = useMemo(() => {
    const result: WordTimestamp[] = [];
    let elapsed = 0;

    scenes.forEach((sc) => {
      const sceneStart = elapsed;
      const dur = sc.duration || 3.5;

      if (sc.word_timings && sc.word_timings.length > 0) {
        sc.word_timings.forEach((w) => {
          result.push({
            word: w.word,
            start: sceneStart + w.start,
            end: sceneStart + w.end
          });
        });
      } else {
        // Fallback word segmentation
        const words = (sc.caption || sc.narration || '').split(/\s+/).filter(Boolean);
        if (words.length > 0) {
          const speechDur = Math.max(1.2, dur - 0.4);
          const wordDur = speechDur / words.length;
          words.forEach((w, idx) => {
            result.push({
              word: w,
              start: sceneStart + idx * wordDur,
              end: sceneStart + (idx + 1) * wordDur
            });
          });
        }
      }
      elapsed += dur;
    });

    return result;
  }, [scenes]);

  // Active scene index
  const activeSceneIndex = useMemo(() => {
    let elapsed = 0;
    for (let i = 0; i < scenes.length; i++) {
      const dur = scenes[i].duration || 3.5;
      if (currentTime >= elapsed && currentTime < elapsed + dur) {
        return i;
      }
      elapsed += dur;
    }
    return Math.max(0, scenes.length - 1);
  }, [currentTime, scenes]);

  const activeScene = scenes[activeSceneIndex] || scenes[0];

  // Playback timer & dynamic ducking update loop
  useEffect(() => {
    let animationFrameId: number;
    let lastTimestamp: number | null = null;

    if (isPlaying) {
      const tick = (timestamp: number) => {
        if (lastTimestamp === null) lastTimestamp = timestamp;
        const delta = (timestamp - lastTimestamp) / 1000;
        lastTimestamp = timestamp;

        setCurrentTime((prev) => {
          const next = prev + delta;
          if (next >= totalDuration) {
            setIsPlaying(false);
            return 0;
          }
          return next;
        });

        animationFrameId = requestAnimationFrame(tick);
      };
      animationFrameId = requestAnimationFrame(tick);
    }

    return () => {
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
    };
  }, [isPlaying, totalDuration]);



  // Canvas dimension classes based on aspect ratio profile
  const canvasSizeStyles = {
    '9:16': 'w-[280px] sm:w-[300px] h-[498px] sm:h-[533px]',
    '16:9': 'w-[340px] sm:w-[500px] h-[191px] sm:h-[281px]',
    '1:1': 'w-[280px] sm:w-[360px] h-[280px] sm:h-[360px]',
  }[currentRatio];

  return (
    <div className="flex flex-col items-center justify-center p-4 bg-slate-950/80 rounded-2xl border border-slate-800 shadow-2xl backdrop-blur-md max-w-xl mx-auto">
      {/* Multi-Format Video Canvas Viewport */}
      <div className={`relative ${canvasSizeStyles} rounded-2xl overflow-hidden bg-black border border-slate-700/60 shadow-inner flex flex-col justify-between transition-all duration-300`}>
        {/* Layer 0: Heavy Blurred Background Fill for 16:9 and 1:1 auto-centering */}
        {activeScene && currentRatio !== '9:16' && (
          <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
            <img
              src={activeScene.image_url}
              alt=""
              className="w-full h-full object-cover blur-2xl scale-125 opacity-40 brightness-75"
            />
            <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />
          </div>
        )}

        {/* Layer 1: Centered Primary Video Frame */}
        {activeScene && (
          <div className={`absolute inset-0 z-0 flex items-center justify-center`}>
            {currentRatio === '9:16' ? (
              <div className="w-full h-full relative">
                <img
                  src={activeScene.image_url}
                  alt={activeScene.narration}
                  className="w-full h-full object-cover transform scale-105 transition-transform duration-1000 ease-out"
                />
                <div className="absolute inset-0 bg-gradient-to-b from-black/50 via-transparent to-black/85 pointer-events-none" />
              </div>
            ) : (
              <div className="h-full aspect-[9/16] relative shadow-2xl rounded-lg overflow-hidden border border-white/10">
                <img
                  src={activeScene.image_url}
                  alt={activeScene.narration}
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black/70 pointer-events-none" />
              </div>
            )}
          </div>
        )}

        {/* Top Bar: Scene Index */}
        <div className="relative z-10 p-3 flex items-center justify-between pointer-events-none">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-900/80 border border-slate-700/60 text-[11px] font-mono text-emerald-400">
            <Sparkles className="w-3 h-3 text-emerald-400" />
            <span>Scene {activeSceneIndex + 1}/{scenes.length}</span>
          </div>
        </div>

        {/* Safe Center-Lower Zone: Viral Hormozi / MrBeast Captions with Dynamic Emojis & 10% Margins */}
        <div className={`relative z-20 px-3 w-full ${currentRatio === '16:9' ? 'pb-3' : 'pb-6 sm:pb-8'}`}>
          <ViralCaptions
            words={allWordTimestamps}
            currentTime={currentTime}
            preset={captionPreset}
            highlightColor={highlightColor}
            chunkSize={currentRatio === '16:9' ? 4 : 3}
          />
        </div>

        {/* Progress Bar */}
        <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-slate-800/80 z-20">
          <div
            className="h-full bg-gradient-to-r from-emerald-500 via-amber-400 to-indigo-500 transition-all duration-75"
            style={{ width: `${(currentTime / Math.max(0.1, totalDuration)) * 100}%` }}
          />
        </div>
      </div>

      {/* Multi-Format Export Profile Switcher Bar */}
      <div className="w-full mt-4 flex items-center justify-between p-2.5 bg-slate-900/80 rounded-xl border border-slate-800">
        <span className="text-xs text-slate-400 font-medium">Export Profile:</span>
        <div className="flex items-center gap-1.5">
          {[
            { id: '9:16' as AspectRatioProfile, label: '9:16 Vertical', icon: Smartphone, desc: 'Reels / Shorts' },
            { id: '16:9' as AspectRatioProfile, label: '16:9 Desktop', icon: Monitor, desc: 'YouTube' },
            { id: '1:1' as AspectRatioProfile, label: '1:1 Square', icon: Square, desc: 'Feed' },
          ].map((prof) => {
            const Icon = prof.icon;
            const isSelected = currentRatio === prof.id;
            return (
              <button
                key={prof.id}
                onClick={() => setCurrentRatio(prof.id)}
                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  isSelected
                    ? 'bg-emerald-500 text-slate-950 shadow-md font-bold'
                    : 'bg-slate-800/60 text-slate-400 hover:text-white'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{prof.id}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Playback Controls */}
      <div className="w-full mt-3 flex items-center justify-between px-2">
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="flex items-center gap-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-xl shadow-md transition-all active:scale-95"
        >
          {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          <span>{isPlaying ? 'Pause' : 'Play Composition'}</span>
        </button>

        <div className="text-xs font-mono text-slate-400">
          {currentTime.toFixed(1)}s / {totalDuration.toFixed(1)}s
        </div>
      </div>

      {/* Preset & Highlight Color Controls */}
      <div className="w-full mt-3 p-3 bg-slate-900/60 rounded-xl border border-slate-800 flex flex-col gap-2.5">
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-400 font-medium flex items-center gap-1.5">
            <Flame className="w-3.5 h-3.5 text-amber-400" />
            Animation Preset:
          </span>
          <div className="flex items-center gap-1">
            {(['Bouncy Pop-in', 'Smooth Slide-up', 'Word-Reveal'] as CaptionPreset[]).map((p) => (
              <button
                key={p}
                onClick={() => setCaptionPreset(p)}
                className={`px-2 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                  captionPreset === p
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                    : 'bg-slate-800/50 text-slate-400 hover:text-white'
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-400 font-medium flex items-center gap-1.5">
            <Palette className="w-3.5 h-3.5 text-emerald-400" />
            Highlight Glow:
          </span>
          <div className="flex items-center gap-1">
            {[
              { label: 'Yellow (#FFE600)', val: 'yellow' as HighlightColor, colorClass: 'bg-[#FFE600]' },
              { label: 'Neon Green', val: 'neon-green' as HighlightColor, colorClass: 'bg-[#00FF66]' },
              { label: 'Cyan Glow', val: 'cyan' as HighlightColor, colorClass: 'bg-[#00F0FF]' },
            ].map((c) => (
              <button
                key={c.val}
                onClick={() => setHighlightColor(c.val)}
                className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                  highlightColor === c.val
                    ? 'bg-slate-800 text-white border border-slate-600'
                    : 'bg-slate-800/40 text-slate-400 hover:text-white'
                }`}
              >
                <span className={`w-2 h-2 rounded-full ${c.colorClass}`} />
                <span>{c.val}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Embedded Audio Subcomponent (Voice Narration Only) */}
      <AudioDuckingEngine
        voiceNarrationSrc={voiceoverUrl}
        narrationSegments={narrationSegments}
        currentFrame={Math.round(currentTime * 30)}
        totalDurationSeconds={totalDuration}
      />
    </div>
  );
};
