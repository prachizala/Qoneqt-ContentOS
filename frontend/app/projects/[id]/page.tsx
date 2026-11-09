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
  Award
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
        {/* Left Column: 9:16 Vertical Video Preview */}
        <div className="lg:col-span-5 space-y-4">
          <div className="p-4 rounded-2xl glass-card border border-slate-800">
            <h2 className="text-sm font-bold text-slate-300 mb-3 flex items-center gap-2">
              <Video className="w-4 h-4 text-sky-400" />
              <span>Vertical Video Canvas (9:16)</span>
            </h2>

            <div className="relative aspect-[9/16] w-full bg-slate-950 rounded-xl overflow-hidden border border-slate-800 flex items-center justify-center">
              {latestVideo?.file_path || latestVideo?.public_url ? (
                <video
                  controls
                  controlsList="nodownload"
                  src={latestVideo?.public_url || `/storage/temp/${projectId}/video_${projectId}.mp4`}
                  poster={`/storage/temp/${projectId}/thumbnail.jpg`}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="text-center p-6 space-y-2">
                  <Loader2 className="w-8 h-8 text-slate-600 animate-spin mx-auto" />
                  <p className="text-xs text-slate-500">Video rendering in progress...</p>
                </div>
              )}
            </div>

            {latestVideo && (
              <div className="mt-3 flex justify-between items-center text-xs text-slate-400 font-mono px-1">
                <span>Res: 1080x1920</span>
                <span>Length: {latestVideo.duration.toFixed(1)}s</span>
                <a
                  href={latestVideo?.public_url || `/storage/temp/${projectId}/video_${projectId}.mp4`}
                  download
                  className="text-sky-400 hover:text-sky-300 flex items-center gap-1"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download</span>
                </a>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Breakdown, QA, & Actions */}
        <div className="lg:col-span-7 space-y-6">
          {/* QA Validation Card */}
          {latestQA && (
            <div className="p-6 rounded-2xl glass-card border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-slate-200 text-sm flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>Automated Quality Assurance Evaluation</span>
                </h3>
                <span
                  className={`px-2.5 py-0.5 text-xs font-bold rounded-full ${
                    latestQA.final_status === 'PASS'
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                      : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                  }`}
                >
                  QA {latestQA.final_status}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-1">
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs">
                  <span className="text-slate-400 block mb-1">Technical Check:</span>
                  <span className="font-bold text-slate-200 flex items-center gap-1.5">
                    {latestQA.technical_status === 'PASS' ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-rose-400" />
                    )}
                    {latestQA.technical_status} (1080x1920, H.264)
                  </span>
                </div>

                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs">
                  <span className="text-slate-400 block mb-1">LLM Content Check:</span>
                  <span className="font-bold text-slate-200 flex items-center gap-1.5">
                    {latestQA.content_status === 'PASS' ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-rose-400" />
                    )}
                    {latestQA.content_status} (Safety & Alignment)
                  </span>
                </div>
              </div>

              {latestQA.issues && latestQA.issues.length > 0 && (
                <div className="pt-2">
                  <span className="text-xs font-semibold text-rose-400 block mb-1">Flagged Issues:</span>
                  <ul className="space-y-1">
                    {latestQA.issues.map((iss, idx) => (
                      <li key={idx} className="text-xs text-slate-300 bg-rose-500/10 p-2 rounded-lg border border-rose-500/20">
                        [{iss.severity}] {iss.check}: {iss.detail}
                      </li>
                    ))}
                  </ul>
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
