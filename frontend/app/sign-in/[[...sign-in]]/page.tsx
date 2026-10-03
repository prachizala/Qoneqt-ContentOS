'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';
import { Sparkles, ArrowRight } from 'lucide-react';

export default function SignInPage() {
  const [email, setEmail] = useState('creator@qoneqt.ai');
  const [name, setName] = useState('Prachi Zala');
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    login(email, name);
    router.push('/dashboard');
  };

  return (
    <div className="min-h-[75vh] flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-slate-900/90 border border-slate-800 rounded-2xl p-8 shadow-2xl glass-card">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
            <Sparkles className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Sign In to Qoneqt</h2>
            <p className="text-xs text-slate-400">Content Factory Local Studio</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Full Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500/50"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500/50"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full mt-2 py-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-sm rounded-xl transition-all shadow-lg shadow-emerald-500/20 flex items-center justify-center gap-2"
          >
            <span>Continue to Dashboard</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
