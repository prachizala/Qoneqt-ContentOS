'use client';

import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Zap, Settings } from 'lucide-react';

interface HeaderUserNavProps {
  onOpenSettings?: () => void;
}

export default function HeaderUserNav({ onOpenSettings }: HeaderUserNavProps) {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated || !user) {
    return (
      <div className="flex items-center gap-3">
        <span className="text-xs text-slate-400">Guest Session</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={onOpenSettings}
        className="flex items-center gap-2.5 bg-slate-950/70 hover:bg-slate-800/80 border border-slate-800 px-3 py-1.5 rounded-xl shadow-inner transition-colors group cursor-pointer"
        title="Open Settings"
      >
        <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-emerald-500 to-indigo-600 flex items-center justify-center text-white font-semibold text-xs shadow-md group-hover:scale-105 transition-transform">
          {user.name.charAt(0)}
        </div>
        <div className="flex flex-col text-left">
          <span className="text-xs font-semibold text-slate-200 leading-tight group-hover:text-white">
            {user.name}
          </span>
          <span className="text-[10px] font-mono text-emerald-400 flex items-center gap-1">
            <Zap className="w-2.5 h-2.5" />
            {user.plan} PLAN ({user.videosLimit} videos/mo)
          </span>
        </div>
        <Settings className="w-3.5 h-3.5 text-slate-500 group-hover:text-slate-300 ml-1 transition-colors" />
      </button>
    </div>
  );
}
