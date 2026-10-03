'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  X,
  User,
  CreditCard,
  Key,
  ShieldCheck,
  Check,
  LogOut,
  Sparkles,
  ExternalLink
} from 'lucide-react';
import Link from 'next/link';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<'profile' | 'usage' | 'api'>('profile');

  // API Keys local state
  const [elevenLabsKey, setElevenLabsKey] = useState('');
  const [openAIKey, setOpenAIKey] = useState('');
  const [pexelsKey, setPexelsKey] = useState('');
  const [isSaved, setIsSaved] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setElevenLabsKey(localStorage.getItem('qoneqt_elevenlabs_key') || '');
      setOpenAIKey(localStorage.getItem('qoneqt_openai_key') || '');
      setPexelsKey(localStorage.getItem('qoneqt_pexels_key') || '');
    }
  }, [isOpen]);

  const handleSaveApiKeys = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('qoneqt_elevenlabs_key', elevenLabsKey);
    localStorage.setItem('qoneqt_openai_key', openAIKey);
    localStorage.setItem('qoneqt_pexels_key', pexelsKey);

    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 2500);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="w-full max-w-2xl bg-[#0B0F17] border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800/80 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
              <Sparkles className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white tracking-wide">Settings & Preferences</h2>
              <p className="text-xs text-slate-400">Manage account, quota limits, and API integrations</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800/60 rounded-xl transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Tabs */}
        <div className="flex border-b border-slate-800/80 bg-slate-900/30 px-6 gap-2">
          <button
            onClick={() => setActiveTab('profile')}
            className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === 'profile'
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <User className="w-3.5 h-3.5" />
            <span>Account & Profile</span>
          </button>

          <button
            onClick={() => setActiveTab('usage')}
            className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === 'usage'
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <CreditCard className="w-3.5 h-3.5" />
            <span>Subscription & Usage</span>
          </button>

          <button
            onClick={() => setActiveTab('api')}
            className={`flex items-center gap-2 px-4 py-3 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === 'api'
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Key className="w-3.5 h-3.5" />
            <span>API & Integrations</span>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* TAB 1: PROFILE */}
          {activeTab === 'profile' && (
            <div className="space-y-5">
              <div className="flex items-center gap-4 p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-emerald-500 to-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-md">
                  {user?.name?.charAt(0) || 'P'}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-white">{user?.name || 'Prachi Zala'}</h3>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {user?.plan || 'CREATOR'} PLAN
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">{user?.email || 'creator@qoneqt.ai'}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-3.5 bg-slate-900/40 border border-slate-800 rounded-xl">
                  <span className="text-[11px] font-mono text-slate-400">ACCOUNT ROLE</span>
                  <p className="text-xs font-semibold text-slate-200 mt-1 flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-sky-400" />
                    {user?.role || 'USER'}
                  </p>
                </div>

                <div className="p-3.5 bg-slate-900/40 border border-slate-800 rounded-xl">
                  <span className="text-[11px] font-mono text-slate-400">MONTHLY VIDEO LIMIT</span>
                  <p className="text-xs font-semibold text-slate-200 mt-1">
                    {user?.videosLimit || 15} Vertical Videos
                  </p>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-800">
                <button
                  onClick={() => {
                    logout();
                    onClose();
                  }}
                  className="w-full py-2.5 px-4 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded-xl text-xs font-semibold transition-colors flex items-center justify-center gap-2"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Sign Out of Session</span>
                </button>
              </div>
            </div>
          )}

          {/* TAB 2: USAGE */}
          {activeTab === 'usage' && (
            <div className="space-y-5">
              <div className="p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-4">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-medium text-slate-300">Monthly Generation Usage</span>
                  <span className="font-mono text-emerald-400 font-bold">
                    {user?.videosUsed || 3} / {user?.videosLimit || 15} Used
                  </span>
                </div>

                {/* Progress Bar */}
                <div className="w-full h-3 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                  <div
                    className="h-full bg-gradient-to-r from-emerald-500 to-indigo-500 rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min(
                        100,
                        ((user?.videosUsed || 3) / (user?.videosLimit || 15)) * 100
                      )}%`
                    }}
                  />
                </div>

                <p className="text-xs text-slate-400 leading-relaxed">
                  Your monthly allocation resets automatically every 30 days. You have{' '}
                  <span className="text-emerald-400 font-bold">
                    {(user?.videosLimit || 15) - (user?.videosUsed || 3)} generations remaining
                  </span>{' '}
                  in your current billing cycle.
                </p>
              </div>

              <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center justify-between">
                <div>
                  <h4 className="text-xs font-bold text-white">Need higher generation volume?</h4>
                  <p className="text-[11px] text-slate-400">Upgrade to Creator or Enterprise plan for priority rendering</p>
                </div>
                <Link
                  href="/pricing"
                  onClick={onClose}
                  className="px-3.5 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold rounded-lg transition-colors flex items-center gap-1.5 shadow-md shadow-emerald-500/20"
                >
                  <span>View Plans</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          )}

          {/* TAB 3: API & INTEGRATIONS */}
          {activeTab === 'api' && (
            <form onSubmit={handleSaveApiKeys} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  ElevenLabs Voice Synthesis API Key
                </label>
                <input
                  type="password"
                  placeholder="el_sk_..."
                  value={elevenLabsKey}
                  onChange={(e) => setElevenLabsKey(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  OpenAI Script Director Key (GPT-4o)
                </label>
                <input
                  type="password"
                  placeholder="sk-proj-..."
                  value={openAIKey}
                  onChange={(e) => setOpenAIKey(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Pexels Stock Video Search API Key
                </label>
                <input
                  type="password"
                  placeholder="563492ad6f91700001000001..."
                  value={pexelsKey}
                  onChange={(e) => setPexelsKey(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-emerald-500/50"
                />
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  className="w-full py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-xl transition-colors shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2"
                >
                  {isSaved ? (
                    <>
                      <Check className="w-4 h-4 text-slate-950" />
                      <span>API Keys Saved Successfully!</span>
                    </>
                  ) : (
                    <span>Save Integration Credentials</span>
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
