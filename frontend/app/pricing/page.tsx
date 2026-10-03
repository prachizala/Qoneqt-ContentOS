'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Check,
  Sparkles,
  Zap,
  ShieldCheck,
  Crown,
  Building2,
  ArrowRight,
  Layers,
  HelpCircle,
  Loader2,
  CheckCircle2
} from 'lucide-react';
import { PRICING_TIERS, MATRIX_FEATURE_ROWS, PricingTier } from '../config/pricingConfig';
import CreatorUpgradeModal from '../components/CreatorUpgradeModal';

export default function PricingPage() {
  const [currentTier, setCurrentTier] = useState<string>('free');
  const [usageData, setUsageData] = useState<{
    monthly_videos_used: number;
    monthly_videos_limit: string | number;
    monthly_videos_remaining: string | number;
    tier_name: string;
  } | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [upgradingId, setUpgradingId] = useState<string | null>(null);
  const [upgradeSuccess, setUpgradeSuccess] = useState<string | null>(null);
  const [isCreatorModalOpen, setIsCreatorModalOpen] = useState<boolean>(false);

  const fetchUsage = async () => {
    try {
      const res = await fetch('/api/subscription/usage');
      if (res.ok) {
        const data = await res.json();
        setCurrentTier(data.tier_id || 'free');
        setUsageData(data);
      }
    } catch (err) {
      console.error('Failed to load subscription usage:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsage();
  }, []);

  const handleSelectTier = async (tierId: string) => {
    if (tierId === currentTier) return;
    if (tierId === 'creator') {
      setIsCreatorModalOpen(true);
      return;
    }
    if (tierId === 'enterprise') {
      alert('Enterprise team contact initiated. Our sales engineers will contact your workspace.');
      return;
    }

    setUpgradingId(tierId);
    setUpgradeSuccess(null);

    try {
      const res = await fetch('/api/subscription/upgrade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tier_id: tierId }),
      });

      if (res.ok) {
        const result = await res.json();
        setCurrentTier(tierId);
        setUpgradeSuccess(`Successfully switched to ${result.subscription.tier_name} plan!`);
        await fetchUsage();
      }
    } catch (err) {
      console.error('Upgrade error:', err);
    } finally {
      setUpgradingId(null);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-12 pb-16">
      {/* Header Banner */}
      <div className="text-center space-y-4 pt-4">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Qoneqt ContentOS — Pricing Concept</span>
        </div>

        <h1 className="text-4xl md:text-5xl font-black text-white tracking-tight">
          Scale Your Automated <span className="bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 via-teal-400 to-indigo-400">Content Engine</span>
        </h1>

        <p className="text-slate-400 text-base max-w-2xl mx-auto">
          Choose the right plan to accelerate your automated AI research, scriptwriting, voice synthesis, and vertical video rendering pipeline.
        </p>
      </div>

      {/* Live Usage Bar */}
      {usageData && (
        <div className="p-6 rounded-2xl glass-card border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-xl border border-emerald-500/20">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Current Workspace Plan:</span>
                <span className="text-xs font-bold font-mono bg-emerald-500/20 text-emerald-300 px-2.5 py-0.5 rounded-full">
                  {usageData.tier_name}
                </span>
              </div>
              <p className="text-sm font-semibold text-slate-200 mt-0.5">
                Monthly AI Videos: <span className="text-emerald-400 font-bold">{usageData.monthly_videos_used}</span> / {usageData.monthly_videos_limit} used ({usageData.monthly_videos_remaining} remaining)
              </p>
            </div>
          </div>

          <Link
            href="/create"
            className="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-5 py-2.5 rounded-xl text-xs transition-colors shadow-lg shadow-emerald-500/20"
          >
            <span>Create New Video</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}

      {/* Success Notification Alert */}
      {upgradeSuccess && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          <span>{upgradeSuccess}</span>
        </div>
      )}

      {/* Pricing Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {PRICING_TIERS.map((tier) => {
          const isCurrent = currentTier === tier.id;
          const isUpgrading = upgradingId === tier.id;

          return (
            <div
              key={tier.id}
              className={`relative rounded-3xl p-6 flex flex-col justify-between transition-all duration-300 ${
                tier.isPopular
                  ? 'bg-gradient-to-b from-slate-900 to-slate-950 border-2 border-emerald-500/80 shadow-2xl shadow-emerald-500/10 scale-[1.02]'
                  : isCurrent
                  ? 'bg-slate-900/90 border-2 border-indigo-500/80 shadow-xl'
                  : 'bg-slate-900/50 border border-slate-800 hover:border-slate-700'
              }`}
            >
              {/* Badge */}
              {tier.badge && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                  <span
                    className={`px-3 py-1 rounded-full text-[11px] font-bold tracking-wide uppercase shadow-md ${
                      tier.isPopular
                        ? 'bg-gradient-to-r from-emerald-500 to-teal-600 text-white'
                        : tier.id === 'pro'
                        ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white'
                        : 'bg-slate-800 text-slate-300 border border-slate-700'
                    }`}
                  >
                    {tier.badge}
                  </span>
                </div>
              )}

              {/* Card Header */}
              <div className="space-y-4 pt-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-xl font-bold text-white">{tier.name}</h3>
                  {tier.id === 'free' && <ShieldCheck className="w-5 h-5 text-slate-400" />}
                  {tier.id === 'creator' && <Sparkles className="w-5 h-5 text-emerald-400" />}
                  {tier.id === 'pro' && <Crown className="w-5 h-5 text-indigo-400" />}
                  {tier.id === 'enterprise' && <Building2 className="w-5 h-5 text-purple-400" />}
                </div>

                <div className="flex items-baseline gap-1">
                  <span className="text-3xl md:text-4xl font-black text-white tracking-tight">{tier.price}</span>
                  {tier.period && <span className="text-xs text-slate-400 font-medium">{tier.period}</span>}
                </div>

                <p className="text-xs text-slate-400 leading-relaxed min-h-[36px]">
                  {tier.description}
                </p>

                {/* Key Highlights */}
                <div className="pt-2 border-t border-slate-800/80 space-y-2.5 text-xs text-slate-300">
                  <div className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span><strong>{tier.features.aiVideos}</strong> Videos</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span><strong>{tier.features.aiScripts}</strong> Scripts</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>Voice: <strong>{tier.features.aiVoice}</strong></span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>Priority: <strong>{tier.features.priorityProcessing}</strong></span>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-6 mt-6 border-t border-slate-800/60">
                <button
                  onClick={() => handleSelectTier(tier.id)}
                  disabled={isCurrent || isUpgrading}
                  className={`w-full py-3 px-4 rounded-xl text-xs font-bold transition-all duration-200 flex items-center justify-center gap-2 ${
                    isCurrent
                      ? 'bg-slate-800 text-slate-400 cursor-default border border-slate-700'
                      : tier.isPopular
                      ? 'bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white shadow-lg shadow-emerald-500/20 hover:scale-[1.02]'
                      : tier.id === 'pro'
                      ? 'bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white shadow-lg shadow-indigo-500/20 hover:scale-[1.02]'
                      : 'bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 hover:scale-[1.01]'
                  }`}
                >
                  {isUpgrading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : isCurrent ? (
                    <span>Current Active Plan</span>
                  ) : (
                    <>
                      <span>{tier.buttonText}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Feature Comparison Table Section */}
      <div className="space-y-6 pt-8">
        <div className="text-center space-y-2">
          <h2 className="text-2xl md:text-3xl font-extrabold text-white">
            Comprehensive Tier Feature Matrix
          </h2>
          <p className="text-xs text-slate-400">
            Compare all platform capabilities, quotas, and processing priorities across subscription tiers.
          </p>
        </div>

        {/* Matrix Table */}
        <div className="rounded-3xl glass-card border border-slate-800 overflow-hidden shadow-2xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/80">
                  <th className="p-4 md:p-5 font-bold text-slate-300 min-w-[200px]">Feature Capability</th>
                  <th className="p-4 md:p-5 font-bold text-slate-200 text-center min-w-[130px]">Free</th>
                  <th className="p-4 md:p-5 font-bold text-emerald-400 text-center min-w-[130px] bg-emerald-500/5">Creator (₹499)</th>
                  <th className="p-4 md:p-5 font-bold text-indigo-400 text-center min-w-[130px]">Pro (₹1,499)</th>
                  <th className="p-4 md:p-5 font-bold text-purple-400 text-center min-w-[130px]">Enterprise</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {MATRIX_FEATURE_ROWS.map((row) => (
                  <tr key={row.key} className="hover:bg-slate-900/40 transition-colors">
                    <td className="p-4 md:p-5 font-semibold text-slate-300 flex items-center gap-2">
                      <Layers className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                      <span>{row.label}</span>
                    </td>
                    {PRICING_TIERS.map((tier) => {
                      const val = tier.features[row.key as keyof typeof tier.features];
                      const isCheck = val === '✓' || val === '✓✓' || val === '✓✓✓';
                      const isDash = val === '—' || val === 'No';

                      return (
                        <td
                          key={tier.id}
                          className={`p-4 md:p-5 text-center font-medium ${
                            tier.isPopular ? 'bg-emerald-500/5 font-bold text-slate-200' : 'text-slate-300'
                          }`}
                        >
                          {isCheck ? (
                            <span className="text-emerald-400 font-bold text-sm">{val}</span>
                          ) : isDash ? (
                            <span className="text-slate-600 font-bold">—</span>
                          ) : (
                            <span>{val}</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Creator Checkout Modal */}
      <CreatorUpgradeModal
        isOpen={isCreatorModalOpen}
        onClose={() => setIsCreatorModalOpen(false)}
        onSuccess={(sub) => {
          setCurrentTier('creator');
          setUpgradeSuccess('Successfully upgraded to Creator Plan!');
          fetchUsage();
        }}
      />
    </div>
  );
}

