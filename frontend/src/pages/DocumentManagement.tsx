import React, { useState, useEffect } from 'react';
import { Upload, FileText, Shield, Search, Trash2, Eye, Lock, Unlock, Plus, MoreVertical, FileUp, HardDrive } from 'lucide-react';
import apiClient from '../api/client';

interface Document {
  id: string;
  name: string;
  size: string;
  status: 'indexed' | 'processing' | 'error';
  permission: 'public' | 'restricted' | 'private';
  updatedAt: string;
}

const DocumentManagement: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get('/documents');
      setDocuments(response.data);
    } catch (error) {
      console.error('Error fetching documents:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsUploading(true);
    // Simulate upload API call
    setTimeout(() => {
      setIsUploading(false);
      fetchDocuments();
    }, 2000);
  };

  const filteredDocs = documents.filter(doc => 
    doc.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="h-full flex flex-col gap-8">
      {/* TOP SECTION: Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold text-slate-100 tracking-tight">Knowledge Base</h1>
          <p className="text-slate-500 text-sm">Manage source documents and indexing status</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="px-3 py-1 bg-slate-900/80 border border-slate-800 rounded-lg text-[11px] font-mono text-slate-500 flex items-center gap-2">
            <HardDrive size={12} />
            Capacity: {documents.length} Objects
          </div>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-8 h-full">
        {/* LEFT PANEL: Control Center */}
        <div className="w-full lg:w-80 flex flex-col gap-6 shrink-0">
          {/* Upload Card */}
          <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-indigo-500/30 transition-colors shadow-sm">
            <div className="flex items-center gap-2 text-slate-100 font-medium mb-6">
              <Upload size={18} className="text-indigo-400" />
              <span>Ingestion Engine</span>
            </div>
            
            <form onSubmit={handleUpload} className="space-y-4">
              <div className="border-2 border-dashed border-slate-800 rounded-xl p-8 text-center hover:border-indigo-500/50 transition-all cursor-pointer bg-slate-950/40 group">
                <input type="file" className="hidden" id="doc-upload" />
                <label htmlFor="doc-upload" className="cursor-pointer flex flex-col items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400 group-hover:scale-110 transition-transform">
                    <FileUp size={24} />
                  </div>
                  <div className="text-sm text-slate-300 font-medium">Drop file here</div>
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider">PDF, TXT, MD supported</div>
                </label>
              </div>
              <button 
                disabled={isUploading}
                className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 text-white rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20"
              >
                {isUploading ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Plus size={16} />}
                {isUploading ? 'Indexing...' : 'Start Ingestion'}
              </button>
            </form>
          </div>

          {/* Filter Card */}
          <div className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-indigo-500/30 transition-colors shadow-sm space-y-6">
            <div className="flex items-center gap-2 text-slate-100 font-medium">
              <Shield size={18} className="text-indigo-400" />
              <span>Access Controls</span>
            </div>
            
            <div className="space-y-2">
              {['All Documents', 'Public Access', 'Restricted', 'Private'].map((filter) => (
                <button 
                  key={filter}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-all ${
                    filter === 'All Documents' 
                    ? 'bg-indigo-500/10 text-indigo-400 ring-1 ring-indigo-500/30' 
                    : 'text-slate-500 hover:bg-slate-800 hover:text-slate-300'
                  }`}
                >
                  {filter}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* RIGHT PANEL: Document Registry */}
        <div className="flex-1 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="relative w-full max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
              <input 
                type="text" 
                placeholder="Filter knowledge base..." 
                className="w-full pl-10 pr-4 py-2 bg-slate-900/80 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder:text-slate-600 focus:ring-2 ring-indigo-500/40 outline-none transition-all"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <button className="p-2 hover:bg-slate-800 rounded-lg text-slate-500 transition-colors">
              <MoreVertical size={18} />
            </button>
          </div>

          <div className="bg-slate-900/40 border border-slate-800 rounded-2xl overflow-hidden backdrop-blur-sm">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-800/30 text-slate-500 uppercase text-[10px] font-bold tracking-widest border-b border-slate-800">
                <tr className="text-slate-500">
                  <th className="px-6 py-4">Document Name</th>
                  <th className="px-6 py-4">Size</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">Permission</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {isLoading ? (
                  <tr>
                    <td colSpan={5} className="py-20 text-center text-slate-500 text-sm animate-pulse">Scanning repository...</td>
                  </tr>
                ) : filteredDocs.length > 0 ? (
                  filteredDocs.map(doc => (
                    <tr key={doc.id} className="hover:bg-slate-800/40 transition-colors group">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <FileText size={18} className="text-indigo-400" />
                          <span className="text-slate-200 font-medium">{doc.name}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-slate-400 text-xs">{doc.size}</td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <div className={`w-1.5 h-1.5 rounded-full ${
                            doc.status === 'indexed' ? 'bg-emerald-500 shadow-[0_0_5px_#10b981]' : 
                            doc.status === 'processing' ? 'bg-amber-500 animate-pulse' : 'bg-red-500'
                          }`} />
                          <span className="text-xs capitalize text-slate-300">{doc.status}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2 px-2 py-1 rounded-md bg-slate-950/50 border border-slate-800 w-fit">
                          {doc.permission === 'public' ? <Unlock size={12} className="text-indigo-400" /> : 
                           doc.permission === 'private' ? <Lock size={12} className="text-red-400" /> : 
                           <Shield size={12} className="text-amber-400" />}
                          <span className="text-[10px] uppercase font-bold text-slate-500">{doc.permission}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-all transform translate-x-2 group-hover:translate-x-0">
                          <button className="p-2 text-slate-500 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-all" title="View Content">
                            <Eye size={14} />
                          </button>
                          <button className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-900/20 rounded-lg transition-all" title="Delete Document">
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-20 text-center text-slate-500 text-sm">
                      No documents found in the registry.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentManagement;