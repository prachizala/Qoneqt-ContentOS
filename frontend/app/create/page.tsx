'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Sparkles,
  Clock,
  Palette,
  MessageSquare,
  Wand2,
  ArrowRight,
  Loader2,
  Lightbulb,
  Zap,
  Crown,
  Flame,
  Mic,
  Check,
  RefreshCw,
  Video
} from 'lucide-react';
import UpgradeModal from '../components/UpgradeModal';

const TRENDING_HOOKS = [
  { category: 'AI 2026', text: '5 Mindblowing AI Breakthroughs in 2026 That Shocked Scientists', emoji: '🤖' },
  { category: 'Tech War', text: 'Why DeepSeek vs OpenAI Changed the Global AI Race Forever', emoji: '⚡' },
  { category: 'Psychology', text: 'The Secret Dopamine Psychology Behind Million-View Short Videos', emoji: '🔥' },
  { category: 'Future Wealth', text: 'How 1-Person AI Companies Are Replacing Entire Agencies Overnight', emoji: '💡' }
];

const VOICE_PRESETS = [
  { id: 'rachel', name: 'Rachel', desc: 'High-Energy & Viral', emoji: '⚡' },
  { id: 'adam', name: 'Adam', desc: 'Deep Documentary Voice', emoji: '🎙️' },
  { id: 'marcus', name: 'Marcus', desc: 'Tech Authority & Crisp', emoji: '🧠' },
  { id: 'elena', name: 'Elena', desc: 'Cinematic Storyteller', emoji: '✨' }
];

const STYLE_PRESETS = [
  { id: 'Cinematic Volumetric', name: 'Cinematic Volumetric', desc: 'Volumetric raytracing & dynamic lighting', tag: 'Most Popular' },
  { id: 'Cyberpunk Neon', name: 'Cyberpunk Neon', desc: 'Futuristic glowing neon & synthwave aesthetics', tag: 'High Retention' },
  { id: 'Photorealistic 3D', name: 'Photorealistic 3D', desc: 'Crisp studio photography & hyper-detail', tag: 'Documentary' },
  { id: 'Minimalist Modern', name: 'Minimalist Modern', desc: 'Clean vector geometry & bold typography', tag: 'Tech & SaaS' }
];

export default function CreateVideoPage() {
  const router = useRouter();

  const [topic, setTopic] = useState('');
  const [duration, setDuration] = useState<number>(30);
  const [tone, setTone] = useState<string>('Viral / Hook Driven');
  const [style, setStyle] = useState<string>('Cinematic Volumetric');
  const [selectedVoice, setSelectedVoice] = useState<string>('rachel');
  const [isEnhancing, setIsEnhancing] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Subscription & Limit state
  const [usageInfo, setUsageInfo] = useState<{
    tier_name: string;
    monthly_videos_used: number;
    monthly_videos_limit: string | number;
    monthly_videos_remaining: string | number;
    limit_reached: boolean;
  } | null>(null);
  const [showUpgradeModal, setShowUpgradeModal] = useState<boolean>(false);

  const fetchUsage = async (signal?: AbortSignal) => {
    try {
      const res = await fetch('/api/subscription/usage', { signal });
      if (res.ok) {
        const data = await res.json();
        setUsageInfo(data);
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        console.error('Failed to load usage info:', err);
      }
    }
  };

  useEffect(() => {
    const controller = new AbortController();
    fetchUsage(controller.signal);
    return () => controller.abort();
  }, []);

  const handleMagicEnhance = () => {
    setIsEnhancing(true);
    setTimeout(() => {
      const current = topic.trim();
      const map: { [k: string]: string } = {
        'ai': '5 Mindblowing AI Breakthroughs in 2026 That Will Shock You',
        'quantum': 'Why Quantum Computing Will Break All Banking Encryption Overnight',
        'crypto': 'The Unspoken Truth About Crypto in 2026: What Top Traders Never Tell You',
        'video': 'The Secret Dopamine Psychology Behind 10M+ View Short-Form Videos'
      };

      let matched = false;
      for (const key of Object.keys(map)) {
        if (current.toLowerCase().includes(key)) {
          setTopic(map[key]);
          matched = true;
          break;
        }
      }

      if (!matched) {
        if (current.length > 4) {
          setTopic(`The Hidden Truth About ${current}: Why 99% of People Get It Completely Wrong`);
        } else {
          setTopic('Why Autonomous AI Agents Are Rewriting Software Architecture Overnight');
        }
      }
      setIsEnhancing(false);
    }, 400);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setSubmitting(true);
    setError(null);

    try {
      const res = await fetch('/api/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          topic: topic.trim(),
          duration: duration,
          tone: tone,
          hookStyle: tone,
          objective: tone,
          audience: 'general',
          aspect_ratio: '9:16',
          language: 'en',
          style: style,
          visualStyle: style,
          voice: selectedVoice,
        }),
      });

      if (!res.ok) {
        let errorMsg = `Failed to create project: HTTP ${res.status}`;
        try {
          const errData = await res.json();
          if (res.status === 403 || errData?.detail?.error === 'TIER_LIMIT_REACHED' || errData?.error === 'TIER_LIMIT_REACHED') {
            setShowUpgradeModal(true);
            const detailMsg = errData?.detail?.message || errData?.message || 'Monthly video generation limit reached.';
            throw new Error(detailMsg);
          }
          if (errData?.detail) {
            errorMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
          }
        } catch (parseErr: any) {
          if (parseErr.message) errorMsg = parseErr.message;
        }
        throw new Error(errorMsg);
      }

      const data = await res.json();
      router.push(`/projects/${data.id}`);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to submit pipeline request');
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-16">
      {/* Header with Plan Badge */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
            <div className="p-2 bg-gradient-to-tr from-emerald-500 to-indigo-600 rounded-xl">
              <Wand2 className="w-6 h-6 text-white" />
            </div>
            <span>Create New AI Video Pipeline</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Input your topic and configuration. AI agents will research, script, generate visuals, render voiceover, and compose your video.
          </p>
        </div>

        {/* Plan Quota Pill */}
        {usageInfo && (
          <div className="flex items-center gap-3 bg-slate-900 border border-slate-800 p-2.5 px-4 rounded-2xl shrink-0">
            <div className="p-1.5 bg-emerald-500/10 text-emerald-400 rounded-lg">
              <Zap className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
                <span>Plan:</span>
                <span className="font-bold text-slate-200">{usageInfo.tier_name}</span>
                <Link href="/pricing" className="text-sky-400 hover:text-sky-300 ml-1 font-semibold">
                  (Upgrade)
                </Link>
              </div>
              <div className="text-xs font-mono font-bold text-emerald-400">
                {usageInfo.monthly_videos_used} / {usageInfo.monthly_videos_limit} Videos Used
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Form Container */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Topic Input with Magic Prompt AI Enhancer */}
        <div className="p-6 rounded-2xl glass-card border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <label className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-emerald-400" />
              <span>Topic / Core Video Concept</span>
            </label>

            <button
              type="button"
              onClick={handleMagicEnhance}
              disabled={isEnhancing}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-gradient-to-r from-amber-500/20 to-purple-500/20 hover:from-amber-500/30 hover:to-purple-500/30 border border-amber-500/40 text-amber-300 transition-all cursor-pointer shadow-sm hover:scale-[1.02]"
            >
              {isEnhancing ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-400" />
              ) : (
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              )}
              <span>{isEnhancing ? 'Synthesizing...' : '✨ Magic Prompt Enhancer'}</span>
            </button>
          </div>

          <div className="relative">
            <textarea
              rows={3}
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. 5 Mindblowing AI Breakthroughs in 2026 (or click any trending idea below)..."
              required
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500/80 focus:ring-1 focus:ring-emerald-500/80 text-sm leading-relaxed"
            />
          </div>

          {/* Trending Hooks & Ideas */}
          <div className="space-y-2 pt-1">
            <div className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
              <Flame className="w-3.5 h-3.5 text-rose-400" />
              <span>Trending Viral Hooks (Click to autofill):</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {TRENDING_HOOKS.map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setTopic(item.text)}
                  className="text-left p-2.5 rounded-xl bg-slate-950/80 hover:bg-slate-900 border border-slate-800/80 hover:border-slate-700 transition-all flex items-start gap-2.5 group cursor-pointer"
                >
                  <span className="text-base select-none shrink-0 group-hover:scale-110 transition-transform">
                    {item.emoji}
                  </span>
                  <div className="min-w-0">
                    <span className="text-[10px] font-mono text-emerald-400 uppercase tracking-wider block font-bold">
                      {item.category}
                    </span>
                    <p className="text-xs text-slate-300 line-clamp-1 group-hover:text-white transition-colors">
                      {item.text}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Neural Voice & Character Selector */}
        <div className="p-6 rounded-2xl glass-card border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Mic className="w-4 h-4 text-indigo-400" />
              <span>AI Neural Voiceover Model</span>
            </label>
            <span className="text-[11px] font-mono text-slate-400">ElevenLabs & Edge-TTS Engine</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {VOICE_PRESETS.map((v) => {
              const isSelected = selectedVoice === v.id;
              return (
                <button
                  key={v.id}
                  type="button"
                  onClick={() => setSelectedVoice(v.id)}
                  className={`p-3 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
                    isSelected
                      ? 'bg-indigo-500/15 border-indigo-500/50 shadow-md ring-1 ring-indigo-500/30'
                      : 'bg-slate-950/80 border-slate-800 hover:border-slate-700 text-slate-300'
                  }`}
                >
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-lg">{v.emoji}</span>
                    {isSelected && (
                      <span className="w-4 h-4 rounded-full bg-indigo-500 text-white flex items-center justify-center text-[10px]">
                        ✓
                      </span>
                    )}
                  </div>
                  <div>
                    <span className="font-bold text-xs text-slate-200 block">{v.name}</span>
                    <span className="text-[10px] text-slate-400 line-clamp-1">{v.desc}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Visual Style Cards */}
        <div className="p-6 rounded-2xl glass-card border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Palette className="w-4 h-4 text-emerald-400" />
              <span>Visual Rendering Aesthetic</span>
            </label>
            <span className="text-[11px] font-mono text-slate-400">9:16 Kinetic Visual Engine</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {STYLE_PRESETS.map((s) => {
              const isSelected = style === s.id;
              return (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => setStyle(s.id)}
                  className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
                    isSelected
                      ? 'bg-emerald-500/15 border-emerald-500/50 shadow-md ring-1 ring-emerald-500/30'
                      : 'bg-slate-950/80 border-slate-800 hover:border-slate-700 text-slate-300'
                  }`}
                >
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="text-[9px] font-mono bg-slate-900 px-2 py-0.5 rounded border border-slate-800 text-emerald-400 font-bold">
                      {s.tag}
                    </span>
                    {isSelected && (
                      <span className="w-4 h-4 rounded-full bg-emerald-500 text-slate-950 flex items-center justify-center text-[10px] font-bold">
                        ✓
                      </span>
                    )}
                  </div>
                  <div>
                    <span className="font-bold text-xs text-slate-200 block">{s.name}</span>
                    <span className="text-[10px] text-slate-400 leading-tight mt-0.5 block">{s.desc}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Duration & Pacing Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Duration Selector */}
          <div className="p-5 rounded-2xl glass-card border border-slate-800 space-y-2">
            <label className="block text-xs font-semibold text-slate-200 flex items-center gap-2">
              <Clock className="w-4 h-4 text-sky-400" />
              <span>Target Duration</span>
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { dur: 15, label: '15s', sub: 'Viral Blitz' },
                { dur: 30, label: '30s', sub: 'Balanced Short' },
                { dur: 60, label: '60s', sub: 'Deep Explainer' }
              ].map((item) => (
                <button
                  key={item.dur}
                  type="button"
                  onClick={() => setDuration(item.dur)}
                  className={`py-2 px-2 rounded-xl text-center border transition-all cursor-pointer ${
                    duration === item.dur
                      ? 'bg-sky-500 text-white border-sky-400 shadow-lg shadow-sky-500/20'
                      : 'bg-slate-950/80 text-slate-400 border-slate-800 hover:bg-slate-900 hover:text-slate-200'
                  }`}
                >
                  <span className="font-bold text-xs block">{item.label}</span>
                  <span className="text-[9px] opacity-80 block">{item.sub}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Narrative Tone */}
          <div className="p-5 rounded-2xl glass-card border border-slate-800 space-y-2">
            <label className="block text-xs font-semibold text-slate-200 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span>Narrative Hook Archetype</span>
            </label>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-slate-200 text-xs focus:outline-none focus:border-purple-500"
            >
              <option value="Viral / Hook Driven">⚡ Pattern Interrupt (Viral / High CTR)</option>
              <option value="Informative & Educational">🧠 Data-Driven & Analytical</option>
              <option value="Engaging Storytelling">🎬 Cinematic Hero's Journey</option>
              <option value="Satirical / Humorous">🔥 Satirical / Curiosity Gap</option>
            </select>
          </div>
        </div>

        {/* Error Alert with Upgrade Trigger */}
        {error && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-xl text-sm flex items-center justify-between gap-4">
            <span>{error}</span>
            <button
              type="button"
              onClick={() => setShowUpgradeModal(true)}
              className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-4 py-1.5 rounded-lg text-xs shrink-0 transition-colors"
            >
              Upgrade Plan
            </button>
          </div>
        )}

        {/* Submit Action Button */}
        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={submitting || !topic.trim()}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-3 bg-gradient-to-r from-emerald-500 via-teal-600 to-indigo-600 hover:from-emerald-600 hover:to-indigo-700 text-white font-bold px-8 py-4 rounded-xl shadow-xl shadow-emerald-500/20 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed hover:scale-[1.01]"
          >
            {submitting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Launching AI Pipeline...</span>
              </>
            ) : (
              <>
                <span>Generate Video Pipeline</span>
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>
        </div>
      </form>

      {/* Upgrade Modal Popup */}
      <UpgradeModal
        isOpen={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
        currentTier={usageInfo?.tier_name || 'Free'}
        usedCount={usageInfo?.monthly_videos_used || 2}
        limitCount={typeof usageInfo?.monthly_videos_limit === 'number' ? usageInfo.monthly_videos_limit : 2}
        onUpgradeSuccess={async () => {
          await fetchUsage();
          setError(null);
        }}
      />
    </div>
  );
}
