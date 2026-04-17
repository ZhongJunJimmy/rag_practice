import React from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { Users, FileText, MessageSquare, Database } from 'lucide-react';

const Layout: React.FC = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', icon: <MessageSquare size={20} />, label: 'Nexus Chat' },
    { path: '/users', icon: <Users size={20} />, label: 'Identity' },
    { path: '/documents', icon: <FileText size={20} />, label: 'Knowledge' },
  ];

  return (
    <div className="flex h-screen bg-[#050b1a] text-slate-200 font-sans selection:bg-blue-500/30 overflow-hidden relative">
      {/* Refined Background: Clean, professional depth */}
      <div className="fixed inset-0 pointer-events-none z-0 bg-[#0f172a]">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,#1e293b_0%,#0f172a_100%)]" />
        <div className="absolute inset-0 opacity-20 bg-[url('https://grainy-gradients.vercel.app/noise')] contrast-150 brightness-100" />
      </div>

      {/* Sidebar: Minimalist & Polished */}
      <aside className="w-64 bg-[#0f172a]/80 backdrop-blur-md border-r border-slate-800 flex flex-col z-20 relative">
        <div className="p-6 flex items-center gap-3">
          <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
            <Database size={20} />
          </div>
          <span className="text-lg font-semibold tracking-tight text-slate-100">
            RAG<span className="text-indigo-400">OS</span>
          </span>
        </div>
        
        <div className="flex-1 px-4 py-6 space-y-8">
          <div>
            <div className="text-[11px] uppercase tracking-wider text-slate-500 font-semibold mb-4 px-2">Main Console</div>
            <div className="space-y-1">
              {/* Placeholder for future sidebar-based a-z navigation if needed */}
              <div className="px-3 py-2 text-xs text-slate-500 italic">Navigation is synced with top bar</div>
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-900/50 border border-slate-800">
            <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981]" />
            <span className="text-xs font-medium text-slate-400">System Ready</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden relative z-10">
        <header className="h-16 bg-[#0f172a]/50 backdrop-blur-md border-b border-slate-800 flex items-center px-8 justify-between z-20">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-widest">
                {navItems.find(i => i.path === location.pathname)?.label || 'Dashboard'}
              </h2>
            </div>
            
            <nav className="flex items-center gap-1 bg-slate-900/80 p-1 rounded-lg border border-slate-800 shadow-inner">
              {navItems.map(item => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200 ${
                    location.pathname === item.path 
                      ? 'bg-indigo-600 text-white shadow-md' 
                      : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  {item.icon}
                  <span className="hidden sm:inline">{item.label}</span>
                </Link>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-md bg-slate-900/50 border border-slate-800">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              <span className="text-[10px] font-medium text-slate-500 uppercase tracking-tighter">System Online</span>
            </div>
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-slate-400 cursor-pointer hover:bg-slate-700 transition-colors">
              AD
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-8 relative">
          {/* Removed max-w-7xl mx-auto to allow pages to define their own structured layout */}
          <div className="h-full animate-in fade-in slide-in-from-bottom-4 duration-700">
            <Outlet />
          </div>
        </main>
      </div>

      {/* No more sci-fi animations, purely professional CSS if needed */}
    </div>
  );
};

export default Layout;