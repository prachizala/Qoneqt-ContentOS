import './globals.css';
import type { Metadata } from 'next';
import { AuthProvider } from './context/AuthContext';
import ClientLayoutShell from './components/ClientLayoutShell';

export const metadata: Metadata = {
  title: 'Qoneqt AI Content Factory',
  description: 'Automated end-to-end short-form video generation & publishing pipeline.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0B0F17] text-slate-100 min-h-screen flex flex-col md:flex-row antialiased">
        <AuthProvider>
          <ClientLayoutShell>{children}</ClientLayoutShell>
        </AuthProvider>
      </body>
    </html>
  );
}
