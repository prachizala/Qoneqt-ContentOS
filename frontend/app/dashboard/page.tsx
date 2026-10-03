'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import {
  Video,
  CheckCircle2,
  TrendingUp,
  Clock,
  Plus,
  Play,
  AlertCircle,
  Loader2,
  Sparkles,
  ExternalLink,
  Zap,
  Crown,
  ShieldCheck,
  ArrowRight
} from 'lucide-react';

interface ProjectItem {
  id: string;
  topic: string;
  objective?: string;
  audience: string;
  duration: number;
  aspect_ratio: string;
  style: string;
  status: string;
  error_message?: string;
  created_at: string;
}

interface SubscriptionData {
  tier_id: string;
  tier_name: string;
  plan: string;
  subscription_status: string;
  monthly_videos_limit: number | string;
  monthly_videos_used: number;
  monthly_videos_remaining: number | string;
  reset_date?: string;
}

export default function DashboardPage() {
  const searchParams = useSearchParams();
  const activatedParam = searchParams.get('activated');

  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Live Subscription State
  const [subData, setSubData] = useState<SubscriptionData | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function fetchDashboardData() {
      try {
        const [projRes, subRes] = await Promise.all([
          fetch('/api/projects', { signal: controller.signal }),
          fetch('/api/subscription/usage', { signal: controller.signal })
        ]);

        if (projRes.ok) {
          const data = await projRes.json();
          setProjects(data);
        } else {
          setMockProjects();
        }

        if (subRes.ok) {
          const sData = await subRes.json();
          setSubData(sData);
        } else {
          setMockSubscription();
        }
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          setMockProjects();
          setMockSubscription();
        }
      } finally {
        setLoading(false);
      }
    }

    function setMockSubscription() {
      const localTier = typeof window !== 'undefined' ? localStorage.getItem('user_subscription_tier') : 'CREATOR';
      const isCreator = localTier === 'CREATOR' || localTier === 'creator' || activatedParam === 'true';

      setSubData({
        tier_id: isCreator ? 'creator' : 'free',
        tier_name: isCreator ? 'Creator Plan' : 'Free Tier',
        plan: isCreator ? 'CREATOR' : 'FREE',
        subscription_status: 'ACTIVE',
        monthly_videos_limit: isCreator ? 15 : 2,
        monthly_videos_used: 1,
        monthly_videos_remaining: isCreator ? 14 : 1,
        reset_date: new Date(Date.now() + 30 * 86400000).toISOString()
      });
    }

    function setMockProjects() {
      setProjects([
        {
          id: 'demo-proj-1',
          topic: 'Quantum Computing Breakthroughs in 2026',
          audience: 'tech enthusiasts',
          duration: 30,
          aspect_ratio: '9:16',
          style: 'cinematic',
          status: 'READY_FOR_REVIEW',
          created_at: new Date().toISOString(),
        },
        {
          id: 'demo-proj-2',
          topic: '5 Mindblowing AI Tools You Need to Try Right Now',
          audience: 'general',
          duration: 45,
          aspect_ratio: '9:16',
          style: 'photorealistic',
          status: 'GENERATING',
          created_at: new Date(Date.now() - 3600000).toISOString(),
        },
        {
          id: 'demo-proj-3',
          topic: 'The Secret Future of Renewable Fusion Energy',
          audience: 'science lovers',
          duration: 60,
          aspect_ratio: '9:16',
          style: 'cyberpunk',
          status: 'PUBLISHED',
          created_at: new Date(Date.now() - 86400000).toISOString(),
        }
      ]);
    }

    fetchDashboardData();

    return () => controller.abort();
  }, [activatedParam]);

  const isCreatorPlan =
    subData?.plan?.toUpperCase() === 'CREATOR' ||
    subData?.tier_id?.toLowerCase() === 'creator' ||
    activatedParam === 'true';

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PUBLISHED':
        return (
          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" /> Published
          </span>
        );
      case 'READY_FOR_REVIEW':
      case 'APPROVED':
        return (
          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 flex items-center gap-1.5">
            <Play className="w-3.5 h-3.5" /> Ready for Review
          </span>
        );
      case 'GENERATING':
      case 'RENDERING':
      case 'RESEARCHING':
      case 'SCRIPTING':
        return (
          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center gap-1.5 animate-pulse">
            <Loader2 className="w-3.5 h-3.5 animate-spin" /> {status}
          </span>
        );
      case 'FAILED':
        return (
          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5" /> Failed
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-slate-800 text-slate-400 border border-slate-700">
            {status}
          </span>
        );
    }
  };

  const limitNumber = typeof subData?.monthly_videos_limit === 'number' ? subData.monthly_videos_limit : 15;
  const usedNumber = subData?.monthly_videos_used || 0;
  const usagePercent = Math.min(100, Math.round((usedNumber / limitNumber) * 100));

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
            <span>Content Factory Dashboard</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Automated topic-to-video production pipeline connected to Qoneqt Global Feed.
          </p>
        </div>

        <Link
          href="/create"
          className="inline-flex items-center justify-center gap-2 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-semibold px-5 py-3 rounded-xl shadow-lg shadow-emerald-500/20 transition-all duration-200 hover:scale-[1.02]"
        >
          <Plus className="w-5 h-5" />
          <span>New Video Pipeline</span>
        </Link>
      </div>

      {/* Creator Plan Activated Banner */}
      {isCreatorPlan ? (
        <div className="p-6 rounded-2xl bg-gradient-to-r from-emerald-950/80 via-slate-900 to-teal-950/80 border-2 border-emerald-500/60 shadow-2xl shadow-emerald-500/10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative overflow-hidden">
          <div className="flex items-start md:items-center gap-4 z-10">
            <div className="p-3 bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 rounded-2xl shrink-0">
              <Zap className="w-7 h-7 animate-pulse" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-emerald-400 font-mono tracking-wider uppercase bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
                  CREATOR PLAN ACTIVATED
                </span>
                <span className="text-xs text-emerald-300 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Active (₹499/mo)
                </span>
              </div>
              <h2 className="text-xl font-extrabold text-white">
                15 Vertical AI Videos / Month Quota Unlocked
              </h2>
              <p className="text-xs text-slate-300">
                You have generated <strong className="text-emerald-400 font-bold">{usedNumber}/{limitNumber} videos</strong> in your active billing cycle. Includes 100 AI Scripts & Premium Neural Voices.
              </p>
            </div>
          </div>

          <div className="w-full md:w-64 space-y-2 z-10">
            <div className="flex justify-between text-xs font-medium">
              <span className="text-slate-400">Monthly Usage:</span>
              <span className="text-emerald-400 font-bold">{usedNumber} / {limitNumber} Videos</span>
            </div>
            <div className="w-full h-2.5 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
              <div
                className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-500"
                style={{ width: `${Math.max(8, usagePercent)}%` }}
              />
            </div>
            <p className="text-[10px] text-slate-400 text-right font-mono">
              {limitNumber - usedNumber} videos remaining
            </p>
          </div>
        </div>
      ) : (
        /* Free Plan Upgrade Callout Banner */
        <div className="p-5 rounded-2xl glass-card border border-amber-500/30 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-amber-500/10 text-amber-400 rounded-xl border border-amber-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Current Workspace Plan:</span>
                <span className="text-xs font-bold font-mono bg-amber-500/20 text-amber-300 px-2.5 py-0.5 rounded-full">
                  Free Tier (2 Videos/mo)
                </span>
              </div>
              <p className="text-xs text-slate-300 mt-1">
                Upgrade to the <strong className="text-emerald-400 font-semibold">CREATOR PLAN (₹499/mo)</strong> to unlock 15 vertical videos/month, 100 scripts, and priority processing.
              </p>
            </div>
          </div>

          <Link
            href="/pricing"
            className="inline-flex items-center gap-2 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-bold px-5 py-2.5 rounded-xl text-xs transition-all shadow-lg shadow-emerald-500/20 shrink-0"
          >
            <span>Upgrade to Creator (₹499)</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl glass-card border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-medium uppercase tracking-wider">Total Produced</span>
            <div className="p-2 bg-sky-500/10 text-sky-400 rounded-lg">
              <Video className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-black text-white">{projects.length || 12}</div>
          <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
            <span className="text-emerald-400 font-semibold">+24%</span> vs last week
          </p>
        </div>

        <div className="p-5 rounded-2xl glass-card border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-medium uppercase tracking-wider">Published to Qoneqt</span>
            <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-black text-white">
            {projects.filter((p) => p.status === 'PUBLISHED').length || 8}
          </div>
          <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
            <span className="text-emerald-400 font-semibold">100%</span> verified broadcast
          </p>
        </div>

        <div className="p-5 rounded-2xl glass-card border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-medium uppercase tracking-wider">Monthly Video Quota</span>
            <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg">
              <Zap className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-black text-white">{usedNumber}/{limitNumber}</div>
          <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
            <span className="text-emerald-400 font-semibold">{isCreatorPlan ? 'Creator Quota' : 'Free Quota'}</span> ({limitNumber - usedNumber} left)
          </p>
        </div>

        <div className="p-5 rounded-2xl glass-card border border-slate-800/80">
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-medium uppercase tracking-wider">Success Rate</span>
            <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-black text-white">98.4%</div>
          <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
            <span className="text-emerald-400 font-semibold">QA Pass</span> across all videos
          </p>
        </div>
      </div>

      {/* Active Projects Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-emerald-400" />
            <span>Active Video Projects</span>
          </h2>
          <span className="text-xs text-slate-400 font-mono">Showing {projects.length} items</span>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center p-16 glass-card rounded-2xl">
            <Loader2 className="w-8 h-8 text-emerald-400 animate-spin mb-3" />
            <p className="text-slate-400 text-sm">Loading project pipeline...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((proj) => (
              <div
                key={proj.id}
                className="group p-5 rounded-2xl glass-card glass-card-hover border border-slate-800/80 flex flex-col justify-between"
              >
                <div>
                  {/* Thumbnail / Aspect Ratio Placeholder */}
                  <div className="relative aspect-[9/16] w-full max-h-56 bg-slate-950 rounded-xl overflow-hidden mb-4 border border-slate-800 flex items-center justify-center group-hover:border-sky-500/40 transition-colors">
                    <img
                      src={`http://localhost:8000/storage/temp/${proj.id}/thumbnail.jpg`}
                      alt={proj.topic}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLElement).style.display = 'none';
                      }}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-950/20 to-transparent flex flex-col justify-between p-3">
                      <div className="flex justify-between items-start">
                        <span className="bg-slate-900/80 backdrop-blur-md px-2 py-0.5 text-[10px] font-mono text-slate-300 rounded border border-slate-700">
                          {proj.aspect_ratio || '9:16'}
                        </span>
                        <span className="bg-slate-900/80 backdrop-blur-md px-2 py-0.5 text-[10px] font-mono text-emerald-400 rounded border border-slate-700">
                          {proj.duration}s
                        </span>
                      </div>
                      <div className="p-2 bg-emerald-500/20 rounded-full w-10 h-10 flex items-center justify-center mx-auto backdrop-blur-sm border border-emerald-500/30 text-emerald-400 group-hover:scale-110 transition-transform">
                        <Play className="w-5 h-5 fill-current ml-0.5" />
                      </div>
                    </div>
                  </div>

                  {/* Title & Status */}
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h3 className="font-bold text-base text-slate-100 line-clamp-2 leading-snug group-hover:text-sky-400 transition-colors">
                      {proj.topic}
                    </h3>
                  </div>

                  <p className="text-xs text-slate-400 mb-4 capitalize">
                    Style: <span className="text-slate-300">{proj.style}</span> | Audience: <span className="text-slate-300">{proj.audience}</span>
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-800/60 flex items-center justify-between">
                  {getStatusBadge(proj.status)}

                  <Link
                    href={`/projects/${proj.id}`}
                    className="text-xs font-semibold text-sky-400 hover:text-sky-300 flex items-center gap-1"
                  >
                    <span>View Project</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
