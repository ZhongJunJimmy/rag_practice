import React, { useState, useEffect, useRef } from 'react';
import { Send, Database, Sparkles, Plus } from 'lucide-react';
import apiClient from '../api/client';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: string[];
}

interface Session {
  id: string;
  title: string;
  lastMessage: string;
  date: string;
}

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessions] = useState<Session[]>([
    { id: '1', title: 'System Architecture Analysis', lastMessage: 'The RAG pipeline is...', date: '2h ago' },
    { id: '2', title: 'Security Protocol Review', lastMessage: 'Access levels are...', date: '5h ago' },
    { id: '3', title: 'Data Indexing Status', lastMessage: 'All documents are...', date: 'Yesterday' },
  ]);
  const [activeSession, setActiveSession] = useState('1');
  const [currentSources, setCurrentSources] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await apiClient.post('/query', { query: input });
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sources: response.data.sources || [],
      };
      setMessages(prev => [...prev, aiMsg]);
      setCurrentSources(aiMsg.sources || []);
    } catch (error) {
      console.error('Query error:', error);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Critical failure in retrieval engine. Please check system logs.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full flex gap-0 overflow-hidden">
      {/* SIDEBAR: History */}
      <div className="w-72 flex flex-col border-r border-slate-800 bg-slate-900/30 backdrop-blur-sm">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-widest text-slate-500">Chat History</h3>
          <button className="p-1.5 bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-400 rounded-lg transition-colors">
            <Plus size={14} />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-3 space-y-1 custom-scrollbar">
          {sessions.map(session => (
            <div 
              key={session.id}
              onClick={() => setActiveSession(session.id)}
              className={`p-3 rounded-lg cursor-pointer transition-all ${
                activeSession === session.id 
                ? 'bg-slate-800 text-slate-100 shadow-sm' 
                : 'text-slate-500 hover:bg-slate-800/50 hover:text-slate-300'
              }`}
            >
              <div className="text-xs font-medium truncate">{session.title}</div>
              <div className="text-[10px] opacity-40 truncate mt-0.5">{session.date}</div>
            </div>
          ))}
        </div>
      </div>

      {/* MAIN CHAT AREA */}
      <div className="flex-1 flex flex-col relative bg-transparent">
        {/* Chat Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
          <div className="max-w-3xl mx-auto w-full space-y-6">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center pt-20 space-y-6">
                <div className="w-12 h-12 rounded-xl bg-indigo-600/10 flex items-center justify-center text-indigo-400">
                  <Sparkles size={24} />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-slate-100">How can I help you today?</h2>
                  <p className="text-slate-500 text-sm mt-2 max-w-sm mx-auto">
                    Query the knowledge base for precise answers synthesized from your documents.
                  </p>
                </div>
              </div>
            ) : (
              messages.map(msg => (
                <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} gap-4`}>
                  {msg.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-lg bg-indigo-600/20 flex items-center justify-center text-indigo-400 shrink-0 mt-1">
                      <Sparkles size={14} />
                    </div>
                  )}
                  <div className={`max-w-[85%] p-4 rounded-2xl ${
                    msg.role === 'user' 
                    ? 'bg-indigo-600 text-white rounded-tr-none shadow-lg shadow-indigo-600/10' 
                    : 'bg-slate-800/50 text-slate-200 border border-slate-700 rounded-tl-none'
                  }`}>
                    <div className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</div>
                    <div className={`text-[10px] mt-2 opacity-40 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                      {msg.timestamp}
                    </div>
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="flex justify-start gap-4">
                <div className="w-8 h-8 rounded-lg bg-indigo-600/20 flex items-center justify-center text-indigo-400 shrink-0 mt-1">
                  <Sparkles size={14} />
                </div>
                <div className="bg-slate-800/50 p-4 rounded-2xl rounded-tl-none border border-slate-700">
                  <div className="flex gap-1.5">
                    <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* INPUT AREA: Floating Style */}
        <div className="p-6">
          <div className="max-w-3xl mx-auto relative">
            <form onSubmit={handleSend} className="relative group">
              <input 
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask your knowledge base..." 
                className="w-full px-5 py-4 pr-14 bg-slate-900 border border-slate-700 rounded-2xl text-sm text-slate-100 outline-none focus:ring-2 ring-indigo-500/40 transition-all placeholder:text-slate-600 shadow-2xl"
              />
              <button 
                type="submit"
                disabled={isLoading || !input.trim()}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white rounded-xl transition-all"
              >
                <Send size={18} />
              </button>
            </form>
            
            {/* SOURCE PREVIEW: Appears when sources are available */}
            {currentSources.length > 0 && (
              <div className="mt-4 p-4 rounded-xl bg-slate-900/80 border border-slate-800 backdrop-blur-sm animate-in fade-in slide-in-from-bottom-2 duration-300">
                <div className="flex items-center gap-2 text-slate-400 mb-3">
                  <Database size={12} />
                  <span className="text-[10px] font-semibold uppercase tracking-widest">Retrieved Context</span>
                </div>
                <div className="grid grid-cols-1 gap-2">
                  {currentSources.map((source, idx) => (
                    <div key={idx} className="p-2 rounded-lg bg-slate-800/50 border border-slate-700 text-xs text-slate-400 italic line-clamp-2 hover:text-slate-200 transition-colors cursor-help">
                      "{source}"
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;