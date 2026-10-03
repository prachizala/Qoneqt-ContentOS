'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import {
  Sparkles,
  Zap,
  Check,
  Crown,
  X,
  ArrowRight,
  Loader2
} from 'lucide-react';
import { PRICING_TIERS } from '../config/pricingConfig';

interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentTier?: string;
  usedCount?: number;
  limitCount?: number;
  onUpgradeSuccess?: (newTier: string) => void;
}

import CreatorUpgradeModal from './CreatorUpgradeModal';

export default function UpgradeModal({
  isOpen,
  onClose,
  currentTier = 'Free',
  usedCount = 2,
  limitCount = 2,
  onUpgradeSuccess
}: UpgradeModalProps) {
  const [upgradingTier, setUpgradingTier] = useState<string | null>(null);
  const [showCreatorCheckout, setShowCreatorCheckout] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleQuickUpgrade = async (tierId: string) => {
    if (tierId === 'creator') {
      setShowCreatorCheckout(true);
      return;
    }

    setUpgradingTier(tierId);
    try {
      const res = await fetch('/api/subscription/upgrade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tier_id: tierId }),
      });

      if (res.ok) {
        if (onUpgradeSuccess) onUpgradeSuccess(tierId);
        onClose();
      }
    } catch (err) {
      console.error('Quick upgrade error:', err);
    } finally {
      setUpgradingTier(null);
    }
  };

  const creatorTier = PRICING_TIERS.find((t) => t.id === 'creator');
  const proTier = PRICING_TIERS.find((t) => t.id === 'pro');

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-xl w-full p-6 md:p-8 space-y-6 shadow-2xl relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="text-center space-y-2 pt-2">
          <div className="inline-flex p-3 bg-gradient-to-tr from-amber-500/20 to-rose-500/20 border border-amber-500/30 text-amber-400 rounded-2xl mb-1">
            <Zap className="w-6 h-6 animate-pulse" />
          </div>
          <h2 className="text-2xl font-black text-white tracking-tight">
            Monthly Video Generation Limit Reached
          </h2>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            You have used <strong className="text-rose-400">{usedCount}/{limitCount} videos</strong> included in your <strong className="text-slate-200">{currentTier}</strong> plan for this month.
          </p>
        </div>

        {/* Tier Cards Comparison */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          {/* Creator Option */}
          {creatorTier && (
            <div className="p-5 rounded-2xl bg-slate-950 border border-emerald-500/40 hover:border-emerald-500/80 transition-colors flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-emerald-400 font-mono uppercase">Creator Plan</span>
                  <span className="text-xs bg-emerald-500/10 text-emerald-300 px-2 py-0.5 rounded-full font-bold">15 Videos/mo</span>
                </div>
                <div className="flex items-baseline gap-1 mt-2">
                  <span className="text-2xl font-extrabold text-white">₹499</span>
                  <span className="text-[10px] text-slate-400">/month</span>
                </div>
                <ul className="space-y-1.5 text-[11px] text-slate-300 mt-3">
                  <li className="flex items-center gap-1.5">
                    <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    <span>15 AI Videos + 100 Scripts</span>
                  </li>
                  <li className="flex items-center gap-1.5">
                    <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    <span>Premium Neural Voices</span>
                  </li>
                  <li className="flex items-center gap-1.5">
                    <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    <span>Autopilot & Priority Queue</span>
                  </li>
                </ul>
              </div>

              <button
                onClick={() => handleQuickUpgrade('creator')}
                disabled={upgradingTier !== null}
                className="w-full py-2.5 px-3 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-bold rounded-xl text-xs shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center gap-2"
              >
                {upgradingTier === 'creator' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                <span>Upgrade to Creator</span>
              </button>
            </div>
          )}

          {/* Pro Option */}
          {proTier && (
            <div className="p-5 rounded-2xl bg-slate-950 border border-indigo-500/40 hover:border-indigo-500/80 transition-colors flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-indigo-400 font-mono uppercase">Pro Plan</span>
                  <span className="text-xs bg-indigo-500/10 text-indigo-300 px-2 py-0.5 rounded-full font-bold">50 Videos/mo</span>
                </div>
                <div className="flex items-baseline gap-1 mt-2">
                  <span className="text-2xl font-extrabold text-white">₹1,499</span>
                  <span className="text-[10px] text-slate-400">/month</span>
                </div>
                <ul className="space-y-1.5 text-[11px] text-slate-300 mt-3">
                  <li className="flex items-center gap-1.5">
                    <Check className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                    <span>50 AI Videos + Unlimited Scripts</span>
                  </li>
                  <li className="flex items-center gap-1.5">
                    <Check className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                    <span>Deep AI Analytics & Insights</span>
                  </li>
                  <li className="flex items-center gap-1.5">
                    <Check className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                    <span>High Priority Processing (✓✓)</span>
                  </li>
                </ul>
              </div>

              <button
                onClick={() => handleQuickUpgrade('pro')}
                disabled={upgradingTier !== null}
                className="w-full py-2.5 px-3 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-bold rounded-xl text-xs shadow-lg shadow-indigo-500/20 transition-all flex items-center justify-center gap-2"
              >
                {upgradingTier === 'pro' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Crown className="w-3.5 h-3.5" />}
                <span>Upgrade to Pro</span>
              </button>
            </div>
          )}
        </div>

        {/* Footer Link */}
        <div className="text-center pt-1 border-t border-slate-800">
          <Link
            href="/pricing"
            onClick={onClose}
            className="text-xs text-slate-400 hover:text-slate-200 inline-flex items-center gap-1 transition-colors"
          >
            <span>View full tier comparison matrix</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>
      </div>

      <CreatorUpgradeModal
        isOpen={showCreatorCheckout}
        onClose={() => setShowCreatorCheckout(false)}
        onSuccess={(sub) => {
          if (onUpgradeSuccess) onUpgradeSuccess('creator');
          onClose();
        }}
      />
    </div>
  );
}

