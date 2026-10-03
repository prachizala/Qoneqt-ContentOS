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
  Crown
} from 'lucide-react';
import UpgradeModal from '../components/UpgradeModal';

const PROMPT_EXAMPLES = [
  '5 Mindblowing AI Breakthroughs Happening in 2026',
  'Why Quantum Computing Will Change Everything Overnight',
  'The Secret Psychology Behind Viral Short-Form Videos',
  'How Autonomous AI Agents Are Rewriting Software Architecture'
];

export default function CreateVideoPage() {
  const router = useRouter();

  const [topic, setTopic] = useState('');
  const [duration, setDuration] = useState<number>(30);
  const [tone, setTone] = useState<string>('Viral / Hook Driven');
  const [style, setStyle] = useState<string>('Cinematic Volumetric');
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
        {/* Topic Input */}
        <div className="p-6 rounded-2xl glass-card border border-slate-800 space-y-3">
          <label className="block text-sm font-semibold text-slate-200 flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-emerald-400" />
            <span>Topic / Video Core Concept</span>
          </label>
          <textarea
            rows={3}
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. 5 Mindblowing AI Breakthroughs in 2026..."
            required
            className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500/80 focus:ring-1 focus:ring-emerald-500/80 text-sm leading-relaxed"
          />

          {/* Prompt Examples */}
          <div className="pt-2">
            <div className="text-xs text-slate-400 font-medium mb-2 flex items-center gap-1.5">
              <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
              <span>Prompt Ideas (Click to use):</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {PROMPT_EXAMPLES.map((example, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setTopic(example)}
                  className="text-xs bg-slate-900 hover:bg-slate-800 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-800 transition-colors text-left"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Options Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Duration Selector */}
          <div className="p-6 rounded-2xl glass-card border border-slate-800 space-y-3">
            <label className="block text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Clock className="w-4 h-4 text-sky-400" />
              <span>Duration</span>
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[15, 30, 60].map((dur) => (
                <button
                  key={dur}
                  type="button"
                  onClick={() => setDuration(dur)}
                  className={`py-2.5 px-3 rounded-xl font-bold text-xs border transition-all ${
                    duration === dur
                      ? 'bg-sky-500 text-white border-sky-400 shadow-lg shadow-sky-500/20'
                      : 'bg-slate-900 text-slate-400 border-slate-800 hover:bg-slate-800 hover:text-slate-200'
                  }`}
                >
                  {dur}s
                </button>
              ))}
            </div>
          </div>

          {/* Tone Selector */}
          <div className="p-6 rounded-2xl glass-card border border-slate-800 space-y-3">
            <label className="block text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span>Tone / Hook Style</span>
            </label>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-slate-200 text-sm focus:outline-none focus:border-purple-500"
            >
              <option value="Viral / Hook Driven">Viral / Hook Driven</option>
              <option value="Informative & Educational">Informative & Educational</option>
              <option value="Engaging Storytelling">Engaging Storytelling</option>
              <option value="Satirical / Humorous">Satirical / Humorous</option>
            </select>
          </div>

          {/* Visual Style Selector */}
          <div className="p-6 rounded-2xl glass-card border border-slate-800 space-y-3">
            <label className="block text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Palette className="w-4 h-4 text-emerald-400" />
              <span>Visual Style</span>
            </label>
            <select
              value={style}
              onChange={(e) => setStyle(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-slate-200 text-sm focus:outline-none focus:border-emerald-500"
            >
              <option value="Cinematic Volumetric">Cinematic Volumetric</option>
              <option value="Photorealistic 3D">Photorealistic 3D</option>
              <option value="Cyberpunk Neon">Cyberpunk Neon</option>
              <option value="Minimalist Modern">Minimalist Modern</option>
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
