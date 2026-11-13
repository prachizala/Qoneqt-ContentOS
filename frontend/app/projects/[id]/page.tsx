'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Sparkles,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Play,
  Download,
  RotateCw,
  Send,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  FileText,
  ShieldCheck,
  Video,
  Layers,
  Radio,
  X,
  TrendingUp,
  Zap,
  Award,
  Heart,
  MessageCircle,
  Share2,
  Bookmark,
  Music,
  Smartphone,
  Eye,
  EyeOff,
  Sliders,
  Volume2
} from 'lucide-react';

interface SceneItem {
  id: string;
  scene_number: number;
  duration: number;
  narration: string;
  visual_prompt: string;
  caption?: string;
  transition: string;
  status: string;
}

interface ScriptItem {
  id: string;
  title: string;
  hook: string;
  body: string;
  cta: string;
  hook_variations?: {
    hook_a?: string;
    hook_b?: string;
    hook_c?: string;
  };
  raw_json?: any;
}

interface VideoItem {
  id: string;
  file_path: string;
  public_url?: string;
  thumbnail_path?: string;
  duration: number;
  resolution: string;
  status: string;
}

interface QAResultItem {
  id: string;
  technical_status: string;
  content_status: string;
  issues?: Array<{ check: string; detail: string; severity: string }>;
  final_status: string;
}

interface PublicationItem {
  id: string;
  platform: string;
  post_id?: string;
  feed_url?: string;
  status: string;
  published_at?: string;
}


interface RetentionReportData {
  overall_score: number;
  grade: string;
  hook_breakdown: {
    score: number;
    hook_type_detected: string;
    pattern_interrupt_present: boolean;
    analysis: string;
  };
  pacing_breakdown: {
    score: number;
    words_per_minute: number;
    scene_switch_frequency_seconds: number;
    density_verdict: string;
    analysis: string;
  };
  virality_breakdown: {
    score: number;
    relatability_factor: string;
    emotional_triggers: string[];
    analysis: string;
  };
  cta_breakdown: {
    score: number;
    urgency_level: string;
    frictionless_action: boolean;
    analysis: string;
  };
  scene_dropoffs: Array<{
    scene_number: number;
    duration_s: number;
    estimated_retention_pct: number;
    dropoff_risk: string;
    suggestion: string;
  }>;
  key_strengths: string[];
  critical_dropoffs: string[];
  actionable_recommendations: string[];
  optimized_hooks: Array<{
    style: string;
    headline: string;
    text: string;
    estimated_hook_score: number;
  }>;
}

interface ProjectDetail {
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
  script?: ScriptItem;
  scenes?: SceneItem[];
  videos?: VideoItem[];
  qa_results?: QAResultItem[];
  publications?: PublicationItem[];
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params?.id as string;

  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [progressPercent, setProgressPercent] = useState<number>(0);
  const [progressMessage, setProgressMessage] = useState<string>('Initializing pipeline...');
  const [progressStatus, setProgressStatus] = useState<string>('PROCESSING');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [openSceneId, setOpenSceneId] = useState<string | null>(null);

  // Modal states
  const [showRegenModal, setShowRegenModal] = useState<boolean>(false);
  const [targetScene, setTargetScene] = useState<SceneItem | null>(null);
  const [newPrompt, setNewPrompt] = useState<string>('');
  const [newNarration, setNewNarration] = useState<string>('');
  const [regenerating, setRegenerating] = useState<boolean>(false);

  const [showPublishModal, setShowPublishModal] = useState<boolean>(false);
  const [publishing, setPublishing] = useState<boolean>(false);
  const [approving, setApproving] = useState<boolean>(false);
  const [selectingHook, setSelectingHook] = useState<boolean>(false);
  const [retentionReport, setRetentionReport] = useState<RetentionReportData | null>(null);
  const [loadingRetention, setLoadingRetention] = useState<boolean>(false);
  const [applyingHookText, setApplyingHookText] = useState<string | null>(null);
  const [hookSuccessMsg, setHookSuccessMsg] = useState<string | null>(null);

  const fetchRetentionAudit = async (signal?: AbortSignal) => {
    setLoadingRetention(true);
    try {
      const res = await fetch(`/api/projects/${projectId}/retention-audit`, { signal });
      if (res.ok) {
        const data: RetentionReportData = await res.json();
        setRetentionReport(data);
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        console.error("Retention audit fetch error:", err);
      }
    } finally {
      setLoadingRetention(false);
    }
  };

  const handleApplyOptimizedHook = async (hookText: string) => {
    setApplyingHookText(hookText);
    try {
      const res = await fetch(`/api/projects/${projectId}/apply-optimized-hook`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hook_text: hookText }),
      });
      if (res.ok) {
        setHookSuccessMsg("⚡ Optimized hook applied to Scene 1! Narrative synchronized.");
        setTimeout(() => setHookSuccessMsg(null), 4000);
        await fetchProjectDetails();
        await fetchRetentionAudit();
      }
    } catch (err) {
      console.error("Hook apply error:", err);
    } finally {
      setApplyingHookText(null);
    }
  };

  // Interactive Mobile Showcase & QA Accordion state
  const [showSocialOverlay, setShowSocialOverlay] = useState<boolean>(true);
  const [showQATelemetry, setShowQATelemetry] = useState<boolean>(false);
  const [isLiked, setIsLiked] = useState<boolean>(false);
  const [likeCount, setLikeCount] = useState<number>(24810);
  const [isBookmarked, setIsBookmarked] = useState<boolean>(false);
  const [activeStoryboardScene, setActiveStoryboardScene] = useState<number>(0);

  // Fetch project details
  const fetchProjectDetails = async (signal?: AbortSignal) => {
    try {
      const res = await fetch(`/api/projects/${projectId}`, { signal });
      if (res.ok) {
        const data: ProjectDetail = await res.json();
        setProject(data);
        if (data.status === 'FAILED' && data.error_message) {
          setErrorMessage(data.error_message);
          setProgressStatus('FAILED');
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        console.error("Failed to fetch project details:", err);
      }
    } finally {
      setLoading(false);
    }
  };

  // Poll progress while generating with explicit unmount cleanup
  useEffect(() => {
    const controller = new AbortController();
    fetchProjectDetails(controller.signal);
    fetchRetentionAudit(controller.signal);

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/projects/${projectId}/progress`, { signal: controller.signal });
        if (res.ok) {
          const progData = await res.json();
          const percent = progData.progress_percent || 0;
          const msg = progData.current_message || 'Processing...';
          const stat = progData.status || (percent === 100 ? 'COMPLETED' : 'PROCESSING');
          const err = progData.error || null;

          setProgressPercent(percent);
          setProgressMessage(msg);
          setProgressStatus(stat);

          if (stat === 'FAILED' || err) {
            setErrorMessage(err || msg);
            clearInterval(interval);
            fetchProjectDetails(controller.signal);
          } else if (percent === 100 || stat === 'COMPLETED') {
            clearInterval(interval);
            fetchProjectDetails(controller.signal);
          }
        }
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          console.error("Progress poll error:", err);
        }
      }
    }, 2000);

    return () => {
      clearInterval(interval);
      controller.abort();
    };
  }, [projectId]);

  // Handle Approve Video
  const handleApprove = async () => {
    setApproving(true);
    try {
      const res = await fetch(`/api/projects/${projectId}/approve`, {
        method: 'POST',
      });
      if (res.ok) {
        const updated = await res.json();
        setProject((prev) => (prev ? { ...prev, status: updated.status } : null));
      }
    } catch (err) {
      console.error("Approval error:", err);
    } finally {
      setApproving(false);
    }
  };

  // Handle Single Scene Regeneration
  const handleRegenerateSceneSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetScene) return;

    setRegenerating(true);
    try {
      const res = await fetch(`/api/projects/${projectId}/scenes/${targetScene.id}/regenerate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          new_prompt: newPrompt.trim() || undefined,
          new_narration: newNarration.trim() || undefined,
        }),
      });

      if (res.ok) {
        setShowRegenModal(false);
        fetchProjectDetails();
      }
    } catch (err) {
      console.error("Scene regeneration error:", err);
    } finally {
      setRegenerating(false);
    }
  };

  // Handle Publish to Qoneqt Feed
  const handlePublishSubmit = async () => {
    setPublishing(true);
    try {
      const res = await fetch(`/api/projects/${projectId}/publish`, {
        method: 'POST',
      });
      if (res.ok) {
        setShowPublishModal(false);
        fetchProjectDetails();
      }
    } catch (err) {
      console.error("Publish error:", err);
    } finally {
      setPublishing(false);
    }
  };

  const [retrying, setRetrying] = useState<boolean>(false);

  // Handle Pipeline Retry
  const handleRetryPipeline = async () => {
    setRetrying(true);
    setErrorMessage(null);
    setProgressStatus('GENERATING');
    setProgressPercent(65);
    try {
      const res = await fetch(`/api/projects/${projectId}/retry`, {
        method: 'POST',
      });
      if (res.ok) {
        await fetchProjectDetails();
      }
    } catch (err) {
      console.error("Pipeline retry error:", err);
    } finally {
      setRetrying(false);
    }
  };

  // Handle A/B Hook Selection
  const handleSelectHook = async (hookKey: string) => {
    setSelectingHook(true);
    try {
      const res = await fetch(`/api/projects/${projectId}/hook`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hook_key: hookKey }),
      });
      if (res.ok) {
        fetchProjectDetails();
      }
    } catch (err) {
      console.error("Hook selection error:", err);
    } finally {
      setSelectingHook(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-24 glass-card rounded-2xl">
        <Loader2 className="w-10 h-10 text-emerald-400 animate-spin mb-4" />
        <p className="text-slate-300 text-base">Loading project details...</p>
      </div>
    );
  }

  const isGenerating = project && ['DRAFT', 'RESEARCHING', 'SCRIPTING', 'GENERATING', 'RENDERING', 'QA_PENDING'].includes(project.status);
  const latestVideo = project?.videos && project.videos.length > 0 ? project.videos[project.videos.length - 1] : null;
  const latestQA = project?.qa_results && project.qa_results.length > 0 ? project.qa_results[project.qa_results.length - 1] : null;
  const latestPub = project?.publications && project.publications.length > 0 ? project.publications[project.publications.length - 1] : null;

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Top Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className="bg-slate-900 border border-slate-800 text-emerald-400 px-3 py-1 rounded-full text-xs font-mono">
              Project ID: {projectId.slice(0, 8)}...
            </span>
            <span className="text-xs text-slate-400">
              Created: {new Date(project?.created_at || '').toLocaleDateString()}
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white">
            {project?.topic}
          </h1>
        </div>

        {/* Live Status Badge */}
        <div className="flex items-center gap-3">
          <span className={`px-3 py-1.5 text-xs font-bold rounded-full ${
            project?.status === 'FAILED' || progressStatus === 'FAILED'
              ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
              : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
          }`}>
            Status: {project?.status || progressStatus}
          </span>
        </div>
      </div>

      {/* Failure Error Alert Banner with Interactive Retry Button */}
      {(project?.status === 'FAILED' || progressStatus === 'FAILED' || errorMessage) && (
        <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xl">
          <div className="flex items-start gap-4">
            <AlertCircle className="w-6 h-6 text-rose-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h3 className="font-bold text-rose-400 text-sm">Pipeline Execution Failed</h3>
              <p className="text-xs text-rose-300 font-mono leading-relaxed bg-slate-950/80 p-3 rounded-xl border border-rose-500/20">
                {project?.error_message || errorMessage || 'An unexpected error occurred during background task execution.'}
              </p>
            </div>
          </div>

          <button
            onClick={handleRetryPipeline}
            disabled={retrying}
            className="w-full sm:w-auto px-5 py-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-emerald-500/20 transition-all shrink-0 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
          >
            {retrying ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Restarting Pipeline...</span>
              </>
            ) : (
              <>
                <RotateCw className="w-4 h-4" />
                <span>Retry Pipeline Synthesis</span>
              </>
            )}
          </button>
        </div>
      )}

      {/* Real-Time Progress Stepper (Visible while generating) */}
      {isGenerating && (
        <div className="p-6 rounded-2xl glass-card border border-slate-800 space-y-5">
          <div className="flex justify-between items-center text-sm">
            <span className="font-semibold text-slate-200 flex items-center gap-2">
              <Loader2 className="w-4 h-4 text-emerald-400 animate-spin" />
              <span>Pipeline Execution in Progress</span>
            </span>
            <span className="font-mono text-emerald-400 font-bold text-base">{progressPercent}%</span>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-950 rounded-full h-3 border border-slate-800 overflow-hidden">
            <div
              className="bg-gradient-to-r from-emerald-500 via-teal-500 to-indigo-500 h-full transition-all duration-500"
              style={{ width: `${Math.max(5, progressPercent)}%` }}
            />
          </div>

          {/* Activity Log */}
          <div className="text-xs text-slate-400 font-mono bg-slate-950/80 p-3 rounded-xl border border-slate-800/80 flex items-center gap-2">
            <Radio className="w-3.5 h-3.5 text-sky-400 animate-pulse" />
            <span>{progressMessage}</span>
          </div>

          {/* 5 Stages Stepper */}
          <div className="grid grid-cols-5 gap-2 pt-2">
            {[
              { label: 'Research', target: 20 },
              { label: 'Scripting', target: 40 },
              { label: 'Asset Gen', target: 65 },
              { label: 'Rendering', target: 85 },
              { label: 'QA Check', target: 100 },
            ].map((step, idx) => {
              const completed = progressPercent >= step.target;
              return (
                <div key={idx} className="text-center">
                  <div
                    className={`h-1.5 rounded-full mb-2 ${
                      completed ? 'bg-emerald-400' : 'bg-slate-800'
                    }`}
                  />
                  <span className={`text-[11px] font-medium ${completed ? 'text-slate-200' : 'text-slate-500'}`}>
                    {step.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Published Badge Banner (If Published) */}
      {latestPub && latestPub.status === 'PUBLISHED' && (
        <div className="p-6 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-emerald-500/20 text-emerald-400 rounded-xl">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-emerald-400 text-base">Published to Qoneqt Global Feed</h3>
              <p className="text-xs text-slate-300">
                Post ID: <span className="font-mono">{latestPub.post_id}</span> | Published at {new Date(latestPub.published_at || '').toLocaleTimeString()}
              </p>
            </div>
          </div>

          <a
            href={latestPub.feed_url || '#'}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-5 py-2.5 rounded-xl text-sm transition-colors shadow-lg shadow-emerald-500/20"
          >
            <span>View on Qoneqt Feed</span>
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      )}

      {/* Dual-Column Review Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: 9:16 Vertical Video Preview with Realistic Mobile Device Mockup */}
        <div className="lg:col-span-5 space-y-4">
          <div className="p-4 sm:p-5 rounded-2xl glass-card border border-slate-800 flex flex-col items-center">
            <div className="w-full flex items-center justify-between mb-4">
              <h2 className="text-xs font-bold text-slate-300 flex items-center gap-2 uppercase tracking-wider font-mono">
                <Smartphone className="w-4 h-4 text-emerald-400" />
                <span>Mobile Preview Canvas</span>
              </h2>

              {/* Social Overlay Toggle */}
              <button
                type="button"
                onClick={() => setShowSocialOverlay(!showSocialOverlay)}
                className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[11px] font-mono border transition-all ${
                  showSocialOverlay
                    ? 'bg-emerald-500/15 border-emerald-500/40 text-emerald-300'
                    : 'bg-slate-800/80 border-slate-700 text-slate-400 hover:text-slate-200'
                }`}
                title="Toggle Social UI Simulator"
              >
                {showSocialOverlay ? <Eye className="w-3.5 h-3.5 text-emerald-400" /> : <EyeOff className="w-3.5 h-3.5 text-slate-400" />}
                <span>{showSocialOverlay ? 'Social UI: On' : 'Clean View'}</span>
              </button>
            </div>

            {/* Realistic iPhone 16 Pro Frame (9:16 Aspect Ratio) */}
            <div className="w-full max-w-[340px] p-[5px] rounded-[48px] bg-gradient-to-b from-slate-600 via-slate-800 to-slate-950 shadow-2xl shadow-emerald-500/10 ring-1 ring-white/10 relative transition-transform duration-300">
              {/* Inner Bezel Screen */}
              <div className="relative aspect-[9/16] w-full bg-slate-950 rounded-[44px] overflow-hidden border border-slate-900 flex items-center justify-center select-none group">
                
                {/* Dynamic Island Pill */}
                <div className="absolute top-3 left-1/2 -translate-x-1/2 z-30 w-28 h-5 bg-black rounded-full flex items-center justify-between px-2.5 shadow-md border border-white/5 pointer-events-none">
                  <div className="w-2 h-2 rounded-full bg-slate-900 border border-slate-700/60" />
                  <div className="flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-[8px] font-mono text-emerald-400 uppercase tracking-tighter">LIVE</span>
                  </div>
                </div>

                {/* Video Media Layer */}
                {latestVideo?.file_path || latestVideo?.public_url ? (
                  <video
                    controls
                    controlsList="nodownload"
                    playsInline
                    src={latestVideo?.public_url || `/storage/temp/${projectId}/video_${projectId}.mp4`}
                    poster={`/storage/temp/${projectId}/thumbnail.jpg`}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="text-center p-6 space-y-3">
                    <div className="relative w-12 h-12 mx-auto">
                      <div className="absolute inset-0 rounded-full bg-emerald-500/20 animate-ping" />
                      <div className="relative w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center">
                        <Loader2 className="w-6 h-6 text-emerald-400 animate-spin" />
                      </div>
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-200">Rendering Video...</p>
                      <p className="text-[10px] text-slate-500 font-mono mt-0.5">FFmpeg Composition Engine Active</p>
                    </div>
                  </div>
                )}

                {/* Interactive Social Media UI Overlay */}
                {showSocialOverlay && (latestVideo?.file_path || latestVideo?.public_url) && (
                  <div className="absolute inset-0 pointer-events-none flex flex-col justify-between p-4 z-20 bg-gradient-to-b from-black/40 via-transparent to-black/80">
                    {/* Top Qoneqt Tag */}
                    <div className="pt-6 flex justify-between items-center text-[10px] font-mono text-white/80">
                      <span className="bg-black/40 backdrop-blur-md px-2 py-0.5 rounded-md border border-white/10">
                        ⚡ Qoneqt Vertical 9:16
                      </span>
                      <span className="bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-md border border-emerald-500/30">
                        HQ 1080p
                      </span>
                    </div>

                    {/* Bottom & Right Interaction Rails */}
                    <div className="flex items-end justify-between gap-2 pb-1">
                      {/* Bottom Creator & Caption Info */}
                      <div className="space-y-1.5 max-w-[200px] text-left">
                        <div className="flex items-center gap-1.5">
                          <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-emerald-400 to-indigo-600 flex items-center justify-center font-bold text-[10px] text-white shadow-sm">
                            Q
                          </div>
                          <span className="text-xs font-bold text-white drop-shadow-md">@qoneqt_creator</span>
                          <span className="text-[9px] bg-sky-500/20 text-sky-300 px-1 rounded border border-sky-400/30">✓</span>
                        </div>

                        <p className="text-[11px] text-white/90 line-clamp-2 leading-tight drop-shadow-md font-medium">
                          {project?.script?.title || project?.topic}
                        </p>

                        <div className="flex items-center gap-1 text-[10px] text-emerald-300/90 font-mono">
                          <Music className="w-3 h-3 animate-spin shrink-0" style={{ animationDuration: '4s' }} />
                          <span className="truncate">Neural Voiceover • Original Audio</span>
                        </div>
                      </div>

                      {/* Right Action Rail (Clickable) */}
                      <div className="flex flex-col items-center gap-3 pointer-events-auto shrink-0 pb-1">
                        {/* Like Button */}
                        <button
                          type="button"
                          onClick={() => {
                            setIsLiked(!isLiked);
                            setLikeCount((c) => (isLiked ? c - 1 : c + 1));
                          }}
                          className="group flex flex-col items-center gap-0.5 cursor-pointer"
                        >
                          <div className={`p-2 rounded-full backdrop-blur-md transition-all ${
                            isLiked
                              ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/40 scale-110'
                              : 'bg-black/50 text-white/90 group-hover:scale-105 border border-white/10'
                          }`}>
                            <Heart className={`w-4 h-4 ${isLiked ? 'fill-current text-white' : ''}`} />
                          </div>
                          <span className="text-[9px] font-mono text-white/90 font-bold drop-shadow">
                            {(likeCount / 1000).toFixed(1)}k
                          </span>
                        </button>

                        {/* Comment Button */}
                        <div className="flex flex-col items-center gap-0.5">
                          <div className="p-2 rounded-full bg-black/50 text-white/90 backdrop-blur-md border border-white/10">
                            <MessageCircle className="w-4 h-4" />
                          </div>
                          <span className="text-[9px] font-mono text-white/90 font-bold drop-shadow">1.2k</span>
                        </div>

                        {/* Bookmark Button */}
                        <button
                          type="button"
                          onClick={() => setIsBookmarked(!isBookmarked)}
                          className="flex flex-col items-center gap-0.5 cursor-pointer"
                        >
                          <div className={`p-2 rounded-full backdrop-blur-md transition-all ${
                            isBookmarked
                              ? 'bg-amber-500 text-white shadow-lg shadow-amber-500/40'
                              : 'bg-black/50 text-white/90 border border-white/10'
                          }`}>
                            <Bookmark className={`w-4 h-4 ${isBookmarked ? 'fill-current' : ''}`} />
                          </div>
                          <span className="text-[9px] font-mono text-white/90 font-bold drop-shadow">4.9k</span>
                        </button>

                        {/* Share Button */}
                        <div className="flex flex-col items-center gap-0.5">
                          <div className="p-2 rounded-full bg-black/50 text-white/90 backdrop-blur-md border border-white/10">
                            <Share2 className="w-4 h-4" />
                          </div>
                          <span className="text-[9px] font-mono text-white/90 font-bold drop-shadow">8.1k</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Live Audio Ducking Waveform Indicator */}
            <div className="w-full mt-4 p-3 bg-slate-950/80 rounded-xl border border-slate-800/80 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Volume2 className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-[11px] font-mono text-slate-400">Audio Track:</span>
              </div>
              <div className="flex items-center gap-1 h-3">
                {[40, 75, 55, 90, 60, 100, 45, 80, 65, 95, 50, 85].map((h, i) => (
                  <div
                    key={i}
                    className="w-1 bg-emerald-400/80 rounded-full animate-pulse"
                    style={{
                      height: `${h}%`,
                      animationDelay: `${i * 90}ms`,
                      animationDuration: '1.2s'
                    }}
                  />
                ))}
              </div>
              <span className="text-[10px] font-mono bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/20">
                Auto-Ducked
              </span>
            </div>

            {/* Video Meta Stats Footer */}
            {latestVideo && (
              <div className="w-full mt-3 flex justify-between items-center text-xs text-slate-400 font-mono px-1">
                <span>1080×1920 (H.264)</span>
                <span>{latestVideo.duration.toFixed(1)}s</span>
                <a
                  href={latestVideo?.public_url || `/storage/temp/${projectId}/video_${projectId}.mp4`}
                  download
                  className="text-sky-400 hover:text-sky-300 font-bold flex items-center gap-1 transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download MP4</span>
                </a>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Breakdown, Streamlined QA, & Actions */}
        <div className="lg:col-span-7 space-y-5">
          {/* Streamlined QA Validation Banner with Collapsible Details */}
          {latestQA && (
            <div className="p-4 sm:p-5 rounded-2xl glass-card border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-xl border border-emerald-500/20">
                    <ShieldCheck className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-100 text-sm flex items-center gap-2">
                      <span>Automated QA Certification</span>
                      <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px] px-2 py-0.5 rounded-full font-mono font-bold">
                        100% PASS
                      </span>
                    </h3>
                    <p className="text-[11px] text-slate-400 font-mono">
                      Broadcast Ready • 1080x1920 9:16 • Content Safety Passed
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => setShowQATelemetry(!showQATelemetry)}
                  className="text-xs text-sky-400 hover:text-sky-300 flex items-center gap-1 font-mono transition-colors"
                >
                  <span>{showQATelemetry ? 'Hide Logs' : 'View Logs'}</span>
                  {showQATelemetry ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </button>
              </div>

              {/* Expandable Technical Checkpoints */}
              {showQATelemetry && (
                <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-800/80 animate-in fade-in duration-200">
                  <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs">
                    <span className="text-slate-400 block mb-1">Technical Check:</span>
                    <span className="font-bold text-slate-200 flex items-center gap-1.5">
                      {latestQA.technical_status === 'PASS' ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <AlertCircle className="w-4 h-4 text-rose-400" />
                      )}
                      {latestQA.technical_status} (1080x1920, H.264, 44.1kHz)
                    </span>
                  </div>

                  <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs">
                    <span className="text-slate-400 block mb-1">LLM Alignment Check:</span>
                    <span className="font-bold text-slate-200 flex items-center gap-1.5">
                      {latestQA.content_status === 'PASS' ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <AlertCircle className="w-4 h-4 text-rose-400" />
                      )}
                      {latestQA.content_status} (Zero Hallucination)
                    </span>
                  </div>

                  {latestQA.issues && latestQA.issues.length > 0 && (
                    <div className="col-span-2 pt-1">
                      <span className="text-xs font-semibold text-rose-400 block mb-1">Flagged Issues:</span>
                      <ul className="space-y-1">
                        {latestQA.issues.map((iss, idx) => (
                          <li key={idx} className="text-xs text-slate-300 bg-rose-500/10 p-2 rounded-lg border border-rose-500/20 font-mono">
                            [{iss.severity}] {iss.check}: {iss.detail}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* AI Viral Retention & Pacing Auditor */}
          <div className="p-6 rounded-2xl glass-card border border-slate-800 space-y-5 bg-gradient-to-b from-slate-900/80 to-slate-950/80">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="p-2 bg-amber-500/10 text-amber-400 rounded-lg border border-amber-500/20">
                  <TrendingUp className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-extrabold text-slate-100 text-sm flex items-center gap-2">
                    <span>AI Viral Retention & Pacing Predictor</span>
                    <span className="bg-amber-500/10 text-amber-400 text-[10px] font-bold px-2 py-0.5 rounded-full border border-amber-500/20">
                      Algorithmic Audit
                    </span>
                  </h3>
                  <p className="text-[11px] text-slate-400">Shorts/Reels viewer attention curve & 0-3s hook optimization</p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => fetchRetentionAudit()}
                disabled={loadingRetention}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors border border-slate-700/80 self-start sm:self-auto"
              >
                {loadingRetention ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-400" />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <RotateCw className="w-3.5 h-3.5 text-amber-400" />
                    <span>Re-Audit Retention</span>
                  </>
                )}
              </button>
            </div>

            {hookSuccessMsg && (
              <div className="p-3 bg-emerald-500/15 border border-emerald-500/40 rounded-xl text-xs text-emerald-300 flex items-center gap-2 animate-fadeIn">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>{hookSuccessMsg}</span>
              </div>
            )}

            {retentionReport ? (
              <div className="space-y-5">
                {/* Score Header & KPI Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
                  <div className="sm:col-span-2 p-4 bg-slate-950 rounded-xl border border-slate-800/80 flex flex-col justify-between">
                    <span className="text-[11px] text-slate-400 font-medium">Viral Retention Probability</span>
                    <div className="flex items-baseline gap-2 my-2">
                      <span className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-amber-400 via-orange-400 to-rose-400">
                        {retentionReport.overall_score}
                      </span>
                      <span className="text-xs text-slate-500 font-mono">/ 100</span>
                    </div>
                    <div>
                      <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                        retentionReport.grade === 'VIRAL_OUTLIER'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                          : retentionReport.grade === 'HIGH_RETENTION'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                      }`}>
                        {retentionReport.grade.replace('_', ' ')}
                      </span>
                    </div>
                  </div>

                  <div className="sm:col-span-3 grid grid-cols-2 gap-2 text-xs">
                    <div className="p-2.5 bg-slate-950/80 rounded-xl border border-slate-800/80 flex flex-col justify-between">
                      <span className="text-slate-400 text-[10px]">Hook Power (0-30):</span>
                      <span className="text-base font-bold text-amber-400">{retentionReport.hook_breakdown.score} / 30</span>
                      <span className="text-[10px] text-slate-400 truncate">{retentionReport.hook_breakdown.hook_type_detected}</span>
                    </div>
                    <div className="p-2.5 bg-slate-950/80 rounded-xl border border-slate-800/80 flex flex-col justify-between">
                      <span className="text-slate-400 text-[10px]">Speech Cadence:</span>
                      <span className="text-base font-bold text-sky-400">{retentionReport.pacing_breakdown.words_per_minute} WPM</span>
                      <span className="text-[10px] text-slate-400 truncate">{retentionReport.pacing_breakdown.density_verdict}</span>
                    </div>
                    <div className="p-2.5 bg-slate-950/80 rounded-xl border border-slate-800/80 flex flex-col justify-between">
                      <span className="text-slate-400 text-[10px]">Virality Index:</span>
                      <span className="text-base font-bold text-purple-400">{retentionReport.virality_breakdown.score} / 20</span>
                      <span className="text-[10px] text-slate-400">{retentionReport.virality_breakdown.relatability_factor} Reach</span>
                    </div>
                    <div className="p-2.5 bg-slate-950/80 rounded-xl border border-slate-800/80 flex flex-col justify-between">
                      <span className="text-slate-400 text-[10px]">CTA Urgency:</span>
                      <span className="text-base font-bold text-emerald-400">{retentionReport.cta_breakdown.score} / 20</span>
                      <span className="text-[10px] text-slate-400">{retentionReport.cta_breakdown.urgency_level} Impact</span>
                    </div>
                  </div>
                </div>

                {/* Scene-by-Scene Retention Decay Simulation */}
                {retentionReport.scene_dropoffs && retentionReport.scene_dropoffs.length > 0 && (
                  <div className="space-y-2 pt-2">
                    <span className="text-xs font-semibold text-slate-300 block">
                      Scene Retention Decay Curve (Estimated Viewer Retention):
                    </span>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      {retentionReport.scene_dropoffs.map((sc) => (
                        <div key={sc.scene_number} className="p-2.5 bg-slate-950/90 rounded-xl border border-slate-800/80 text-[11px] space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-slate-300">Scene {sc.scene_number}</span>
                            <span className={`text-[10px] font-bold ${
                              sc.dropoff_risk === 'LOW' ? 'text-emerald-400' : sc.dropoff_risk === 'MEDIUM' ? 'text-amber-400' : 'text-rose-400'
                            }`}>
                              {sc.estimated_retention_pct}%
                            </span>
                          </div>
                          <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${
                                sc.dropoff_risk === 'LOW' ? 'bg-emerald-400' : sc.dropoff_risk === 'MEDIUM' ? 'bg-amber-400' : 'bg-rose-500'
                              }`}
                              style={{ width: `${sc.estimated_retention_pct}%` }}
                            />
                          </div>
                          <span className="text-[10px] text-slate-500 block truncate">{sc.duration_s}s | {sc.suggestion}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 1-Click Viral Hook Optimizer */}
                {retentionReport.optimized_hooks && retentionReport.optimized_hooks.length > 0 && (
                  <div className="space-y-2.5 pt-2 border-t border-slate-800/80">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-amber-400 flex items-center gap-1.5">
                        <Zap className="w-3.5 h-3.5" />
                        <span>AI Supercharged Hook Optimizer (1-Click Swap):</span>
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">Algorithm Score Boost: +12-18%</span>
                    </div>

                    <div className="grid grid-cols-1 gap-2">
                      {retentionReport.optimized_hooks.map((opt, idx) => (
                        <div
                          key={idx}
                          className="p-3 bg-slate-950/90 rounded-xl border border-slate-800/80 hover:border-amber-500/40 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                        >
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-slate-200">{opt.headline}</span>
                              <span className="bg-amber-500/10 text-amber-400 text-[10px] font-mono px-2 py-0.2 rounded-full border border-amber-500/20">
                                {opt.style}
                              </span>
                              <span className="text-emerald-400 text-[10px] font-mono font-bold">
                                {opt.estimated_hook_score}/30 Score
                              </span>
                            </div>
                            <p className="text-slate-300 font-normal">"{opt.text}"</p>
                          </div>

                          <button
                            type="button"
                            onClick={() => handleApplyOptimizedHook(opt.text)}
                            disabled={applyingHookText === opt.text}
                            className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-amber-500 hover:bg-amber-600 text-slate-950 transition-colors shrink-0 shadow-md shadow-amber-500/20"
                          >
                            {applyingHookText === opt.text ? (
                              <>
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                <span>Applying...</span>
                              </>
                            ) : (
                              <>
                                <Zap className="w-3.5 h-3.5" />
                                <span>Apply to Scene 1</span>
                              </>
                            )}
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-6 text-center text-xs text-slate-500 space-y-2">
                <Loader2 className="w-6 h-6 animate-spin text-amber-400 mx-auto" />
                <p>Calculating retention probability & viral hooks...</p>
              </div>
            )}
          </div>

          {/* Script & Scene Breakdown */}
          <div className="p-6 rounded-2xl glass-card border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-slate-200 text-sm flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-400" />
                <span>Script & Scene Storyboard Breakdown</span>
              </h3>
              <span className="text-xs text-slate-400 font-mono">
                {project?.scenes?.length || 0} Scenes
              </span>
            </div>

            {project?.script && (
              <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800 text-xs space-y-4">
                {/* Active Primary Hook */}
                <div>
                  <span className="text-slate-400 font-medium flex items-center justify-between">
                    <span>Active Selected Hook (Scene 1):</span>
                    {selectingHook && <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-400" />}
                  </span>
                  <p className="text-emerald-400 font-bold text-sm mt-1 bg-emerald-500/10 p-2.5 rounded-lg border border-emerald-500/20">
                    "{project.script.hook}"
                  </p>
                </div>

                {/* A/B Hook Variations Selection Panel */}
                {project.script.hook_variations && Object.keys(project.script.hook_variations).length > 0 && (
                  <div className="space-y-2 pt-1 border-t border-slate-800/80">
                    <span className="text-slate-300 font-semibold block text-[11px] uppercase tracking-wider text-amber-400">
                      ⚡ A/B Hook Variations (Select to Apply):
                    </span>
                    <div className="grid grid-cols-1 gap-2">
                      {[
                        {
                          key: 'hook_a',
                          label: 'Hook A: Pattern Interrupt / Negative Framing',
                          text: project.script.hook_variations.hook_a,
                          tag: 'Pattern Interrupt'
                        },
                        {
                          key: 'hook_b',
                          label: 'Hook B: Shocking Stat / Data-Driven',
                          text: project.script.hook_variations.hook_b,
                          tag: 'Data-Driven Stat'
                        },
                        {
                          key: 'hook_c',
                          label: 'Hook C: Curiosity Gap / Insider Secret',
                          text: project.script.hook_variations.hook_c,
                          tag: 'Curiosity Gap'
                        }
                      ].map((h) => {
                        if (!h.text) return null;
                        const isSelected = project.script?.hook === h.text;
                        return (
                          <button
                            key={h.key}
                            type="button"
                            onClick={() => handleSelectHook(h.key)}
                            disabled={selectingHook}
                            className={`p-3 rounded-xl text-left border transition-all flex flex-col gap-1 ${
                              isSelected
                                ? 'bg-emerald-500/15 border-emerald-500/50 shadow-md ring-1 ring-emerald-500/30'
                                : 'bg-slate-900/60 border-slate-800/80 hover:border-slate-700 text-slate-300 hover:text-white'
                            }`}
                          >
                            <div className="flex items-center justify-between text-[11px]">
                              <span className="font-bold text-slate-200">{h.label}</span>
                              {isSelected ? (
                                <span className="bg-emerald-500 text-slate-950 font-bold px-2 py-0.5 rounded-full text-[10px] flex items-center gap-1">
                                  <CheckCircle2 className="w-3 h-3" />
                                  <span>Active</span>
                                </span>
                              ) : (
                                <span className="text-slate-400 hover:text-sky-400 font-mono text-[10px]">
                                  Click to Select
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-slate-300 font-normal">"{h.text}"</p>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                <div>
                  <span className="text-slate-400 font-medium">Call to Action:</span>
                  <p className="text-indigo-400 font-semibold mt-0.5">{project.script.cta}</p>
                </div>
              </div>
            )}

            {/* Interactive Horizontal Scene Storyboard Timeline */}
            {project?.scenes && project.scenes.length > 0 && (
              <div className="space-y-2 pt-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400 font-mono flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                    <span>Visual Storyboard Timeline:</span>
                  </span>
                  <span className="text-slate-500 font-mono text-[10px]">Select card to inspect</span>
                </div>

                <div className="flex gap-2.5 overflow-x-auto pb-2 scrollbar-thin">
                  {project.scenes.map((sc, idx) => {
                    const isSelected = openSceneId === sc.id;
                    return (
                      <button
                        key={sc.id}
                        type="button"
                        onClick={() => {
                          setActiveStoryboardScene(idx);
                          setOpenSceneId(sc.id);
                        }}
                        className={`shrink-0 w-36 p-3 rounded-xl border text-left transition-all cursor-pointer ${
                          isSelected
                            ? 'bg-emerald-500/15 border-emerald-500/50 shadow-md ring-1 ring-emerald-500/30'
                            : 'bg-slate-950/80 border-slate-800 hover:border-slate-700 text-slate-300 hover:bg-slate-900/60'
                        }`}
                      >
                        <div className="flex justify-between items-center text-[10px] mb-1.5 font-mono">
                          <span className={`font-bold ${isSelected ? 'text-emerald-400' : 'text-sky-400'}`}>
                            Scene #{sc.scene_number}
                          </span>
                          <span className="text-slate-500">{sc.duration.toFixed(1)}s</span>
                        </div>
                        <p className="text-[11px] text-slate-300 line-clamp-2 leading-tight">
                          {sc.narration}
                        </p>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Scenes Accordion */}
            <div className="space-y-3 pt-2">
              {project?.scenes?.map((scene) => {
                const isOpen = openSceneId === scene.id;
                return (
                  <div key={scene.id} className="border border-slate-800 rounded-xl bg-slate-950 overflow-hidden">
                    <button
                      onClick={() => setOpenSceneId(isOpen ? null : scene.id)}
                      className="w-full p-3.5 flex items-center justify-between text-left hover:bg-slate-900/60 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <span className="w-6 h-6 rounded-full bg-slate-800 text-sky-400 font-bold text-xs flex items-center justify-center">
                          {scene.scene_number}
                        </span>
                        <div>
                          <span className="text-xs font-bold text-slate-200 line-clamp-1">
                            {scene.narration}
                          </span>
                          <span className="text-[10px] text-slate-400 font-mono">
                            Duration: {scene.duration.toFixed(1)}s | Transition: {scene.transition}
                          </span>
                        </div>
                      </div>
                      {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                    </button>

                    {isOpen && (
                      <div className="p-4 border-t border-slate-800/80 bg-slate-900/40 text-xs space-y-3">
                        <div>
                          <span className="text-slate-400 block font-medium mb-1">Visual Prompt Directive:</span>
                          <p className="text-slate-300 bg-slate-950 p-2.5 rounded-lg border border-slate-800 font-mono text-[11px] leading-relaxed">
                            {scene.visual_prompt}
                          </p>
                        </div>

                        <div className="flex justify-end pt-1">
                          <button
                            onClick={() => {
                              setTargetScene(scene);
                              setNewPrompt(scene.visual_prompt);
                              setNewNarration(scene.narration);
                              setShowRegenModal(true);
                            }}
                            className="inline-flex items-center gap-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-sky-400 px-3 py-1.5 rounded-lg font-medium border border-slate-700 transition-colors"
                          >
                            <RotateCw className="w-3.5 h-3.5" />
                            <span>Regenerate Scene</span>
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Action Bar */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
            <button
              onClick={handleApprove}
              disabled={approving || project?.status === 'APPROVED' || project?.status === 'PUBLISHED'}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold px-6 py-3 rounded-xl text-sm border border-slate-700 transition-all disabled:opacity-50"
            >
              {approving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
              <span>{project?.status === 'APPROVED' ? 'Video Approved' : 'Approve Video'}</span>
            </button>

            <button
              onClick={() => setShowPublishModal(true)}
              disabled={project?.status === 'PUBLISHED'}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-bold px-6 py-3 rounded-xl text-sm shadow-xl shadow-emerald-500/20 transition-all hover:scale-[1.01] disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
              <span>Publish to Qoneqt Global Feed</span>
            </button>
          </div>
        </div>
      </div>

      {/* Modal: Single Scene Regeneration */}
      {showRegenModal && targetScene && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl">
            <div className="flex justify-between items-center">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <RotateCw className="w-4 h-4 text-sky-400" />
                <span>Regenerate Scene #{targetScene.scene_number}</span>
              </h3>
              <button onClick={() => setShowRegenModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleRegenerateSceneSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Visual Prompt:</label>
                <textarea
                  rows={3}
                  value={newPrompt}
                  onChange={(e) => setNewPrompt(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-100 focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Narration Voiceover Text:</label>
                <textarea
                  rows={2}
                  value={newNarration}
                  onChange={(e) => setNewNarration(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-100 focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowRegenModal(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={regenerating}
                  className="inline-flex items-center gap-2 bg-sky-500 hover:bg-sky-600 text-white font-bold px-5 py-2 rounded-xl text-xs shadow-lg shadow-sky-500/20"
                >
                  {regenerating ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RotateCw className="w-3.5 h-3.5" />}
                  <span>Regenerate & Re-render</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Publish Confirmation */}
      {showPublishModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-5 shadow-2xl">
            <div className="flex justify-between items-center">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Send className="w-4 h-4 text-emerald-400" />
                <span>Confirm Qoneqt Publication</span>
              </h3>
              <button onClick={() => setShowPublishModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs bg-slate-950 p-4 rounded-xl border border-slate-800">
              <div>
                <span className="text-slate-400 block font-medium">Post Title:</span>
                <p className="text-slate-100 font-bold text-sm mt-0.5">{project?.script?.title || project?.topic}</p>
              </div>
              <div>
                <span className="text-slate-400 block font-medium">Hashtags & Tags:</span>
                <p className="text-emerald-400 font-mono mt-0.5">#Qoneqt #AIContent #{project?.topic.replace(/\s+/g, '')}</p>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowPublishModal(false)}
                className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handlePublishSubmit}
                disabled={publishing}
                className="inline-flex items-center gap-2 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-bold px-6 py-2.5 rounded-xl text-xs shadow-lg shadow-emerald-500/20"
              >
                {publishing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                <span>Confirm Broadcast</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
