import React, { useState, useEffect } from 'react';
import { Users, ShieldCheck, Layers, Search, Plus, Edit2, Trash2 } from 'lucide-react';
import apiClient from '../api/client';

interface User {
  id: string;
  username: string;
  group: string;
  role: string;
  status: 'Active' | 'Inactive';
}

interface RawUser {
  id: string;
  username: string;
  group: string;
  role?: string;
  status?: string;
}

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get('/users');
      // Assuming API returns basic user info, we might need to map it or add defaults for the UI
      const data = response.data.map((u: RawUser) => ({
        ...u,
        status: (u.status as 'Active' | 'Inactive') || 'Active', // Default to Active if not provided by API
        role: u.role || 'Standard'
      }));
      setUsers(data);
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredUsers = users.filter(u => 
    u.username.toLowerCase().includes(searchTerm.toLowerCase()) || 
    u.group.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="h-full flex flex-col gap-8">
      {/* TOP SECTION: Header & Stats */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold text-slate-100 tracking-tight">Identity Management</h1>
          <p className="text-slate-500 text-sm">Configure user access levels and group-based permissions</p>
        </div>
        <button className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-all flex items-center gap-2 shadow-lg shadow-indigo-600/20 w-fit">
          <Plus size={16} />
          Provision New User
        </button>
      </div>

      {/* BENTO STATS GRID */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-indigo-500/30 transition-colors group">
          <div className="flex items-center justify-between mb-3">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
              <Users size={20} />
            </div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Population</span>
          </div>
          <div className="text-2xl font-semibold text-slate-100">{users.length} <span className="text-slate-500 text-sm font-normal">Total Users</span></div>
        </div>
        <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-indigo-500/30 transition-colors group">
          <div className="flex items-center justify-between mb-3">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <ShieldCheck size={20} />
            </div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Security</span>
          </div>
          <div className="text-2xl font-semibold text-slate-100">
            {users.filter(u => u.status === 'Active').length} <span className="text-slate-500 text-sm font-normal">Active Identities</span>
          </div>
        </div>
        <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800 hover:border-indigo-500/30 transition-colors group">
          <div className="flex items-center justify-between mb-3">
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
              <Layers size={20} />
            </div>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Organization</span>
          </div>
          <div className="text-2xl font-semibold text-slate-100">
            {[...new Set(users.map(u => u.group))].length} <span className="text-slate-500 text-sm font-normal">Active Groups</span>
          </div>
        </div>
      </div>

      {/* MAIN CONTENT: User Table */}
      <div className="flex-1 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="relative w-full max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
            <input 
              type="text"
              placeholder="Filter identities..."
              className="w-full pl-10 pr-4 py-2 bg-slate-900/80 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder:text-slate-600 focus:ring-2 ring-indigo-500/40 outline-none transition-all"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        <div className="bg-slate-900/40 border border-slate-800 rounded-2xl overflow-hidden backdrop-blur-sm">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-800/30 text-slate-500 uppercase text-[10px] font-bold tracking-widest border-b border-slate-800">
              <tr>
                <th className="px-6 py-4">Identity</th>
                <th className="px-6 py-4">Group Assignment</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 text-right">Operations</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {isLoading ? (
                <tr>
                  <td colSpan={4} className="py-12 text-center text-slate-500 text-sm">Loading identity registry...</td>
                </tr>
              ) : filteredUsers.map(user => (
                <tr key={user.id} className="hover:bg-slate-800/40 transition-colors group">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-slate-400 group-hover:text-indigo-400 transition-colors">
                        {user.username.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <div className="text-slate-200 font-medium">{user.username}</div>
                        <div className="text-slate-500 text-[11px]">ID: {user.id}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-1 bg-indigo-500/10 text-indigo-400 rounded-md text-[10px] font-semibold border border-indigo-500/20">
                        {user.group}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className={`w-1.5 h-1.5 rounded-full ${user.status === 'Active' ? 'bg-emerald-500 shadow-[0_0_5px_#10b981]' : 'bg-slate-600'}`} />
                      <span className={`text-xs ${user.status === 'Active' ? 'text-slate-300' : 'text-slate-500'}`}>{user.status}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-all transform translate-x-2 group-hover:translate-x-0">
                      <button className="p-2 text-slate-500 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-all">
                        <Edit2 size={14} />
                      </button>
                      <button className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-900/20 rounded-lg transition-all">
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!isLoading && filteredUsers.length === 0 && (
            <div className="py-12 text-center text-slate-500 text-sm">
              No matching identities found in the directory.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserManagement;