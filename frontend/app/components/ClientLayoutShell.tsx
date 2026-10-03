'use client';

import React, { useState, memo } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import HeaderUserNav from './HeaderUserNav';
import SettingsModal from './SettingsModal';
import {
  LayoutDashboard,
  Library,
  Settings,
  Sparkles,
  PlusCircle,
  Radio,
  CreditCard,
} from 'lucide-react';

const Sidebar = memo(({ onOpenSettings }: { onOpenSettings: () => void }) => {
  const pathname = usePathname();

  return (
    <aside className="w-full md:w-64 bg-slate-900/60 border-b md:border-b-0 md:border-r border-slate-800/80 p-5 flex flex-col justify-between shrink-0 glass-card">
      <div>
        {/* Logo */}
        <Link href="/dashboard" prefetch className="flex items-center gap-3 px-2 py-3 mb-8 group">
          <div className="p-2 bg-gradient-to-tr from-emerald-500 to-indigo-600 rounded-xl shadow-lg group-hover:scale-105 transition-transform">
            <Sparkles className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-base text-white tracking-wide leading-tight">Qoneqt AI</h1>
            <p className="text-xs text-emerald-400 font-mono">Content Factory</p>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav className="space-y-1.5">
          <Link
            href="/dashboard"
            prefetch
            className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              pathname === '/dashboard'
                ? 'bg-slate-800/80 text-white font-semibold border border-slate-700'
                : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <LayoutDashboard className="h-4 w-4 text-sky-400" />
            <span>Dashboard</span>
          </Link>

          <Link
            href="/create"
            prefetch
            className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-semibold transition-colors ${
              pathname === '/create'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20'
            }`}
          >
            <PlusCircle className="h-4 w-4 text-emerald-400" />
            <span>New Video</span>
          </Link>

          <Link
            href="/dashboard"
            prefetch
            className="flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
          >
            <Library className="h-4 w-4 text-indigo-400" />
            <span>Content Library</span>
          </Link>

          <Link
            href="/pricing"
            prefetch
            className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
              pathname === '/pricing'
                ? 'bg-slate-800/80 text-white font-semibold border border-slate-700'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <CreditCard className="h-4 w-4 text-emerald-400" />
            <span>Pricing & Plans</span>
          </Link>

          <button
            onClick={onOpenSettings}
            className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors text-left cursor-pointer"
          >
            <Settings className="h-4 w-4 text-slate-400" />
            <span>Settings</span>
          </button>
        </nav>
      </div>

      {/* System Status Footer Badge */}
      <div className="pt-6 mt-6 border-t border-slate-800/60 px-2">
        <div className="flex items-center gap-2.5 text-xs text-slate-400 bg-slate-950/80 px-3 py-2 rounded-lg border border-slate-800/80">
          <Radio className="h-3.5 w-3.5 text-emerald-400 animate-pulse" />
          <span className="font-mono">Engine: Online (v1.0)</span>
        </div>
      </div>
    </aside>
  );
});

Sidebar.displayName = 'Sidebar';

export default function ClientLayoutShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  return (
    <div className="bg-[#0B0F17] text-slate-100 min-h-screen flex flex-col md:flex-row antialiased">
      <Sidebar onOpenSettings={() => setIsSettingsOpen(true)} />

      {/* Main Content Viewport with Header Bar */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b border-slate-800/80 px-6 md:px-10 flex items-center justify-between bg-slate-900/40 backdrop-blur-md sticky top-0 z-40">
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Local Mode
            </span>
          </div>

          <HeaderUserNav onOpenSettings={() => setIsSettingsOpen(true)} />
        </header>

        <main className="flex-1 p-6 md:p-10 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </div>
  );
}
