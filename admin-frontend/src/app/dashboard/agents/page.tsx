'use client';

import { useState, useEffect } from 'react';
import { agentsAPI } from '@/lib/api';
import { Plus, Server } from 'lucide-react';

interface Agent {
  id: number;
  name: string;
  is_active: boolean;
  last_sync?: string;
  created_at: string;
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [agentName, setAgentName] = useState('');

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      const response = await agentsAPI.list();
      setAgents(response.data.data || []);
    } catch (error) {
      console.error('Failed to load agents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await agentsAPI.register(agentName);
      setAgentName('');
      setShowForm(false);
      loadAgents();
    } catch (error) {
      console.error('Failed to register agent:', error);
    }
  };

  return (
    <div className="px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-4xl font-bold text-slate-900">Agents</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition"
        >
          <Plus size={20} />
          Register Agent
        </button>
      </div>

        {showForm && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-xl font-bold text-slate-900 mb-4">Register New Agent</h2>
            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Agent Name</label>
                <input
                  type="text"
                  value={agentName}
                  onChange={(e) => setAgentName(e.target.value)}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                  placeholder="e.g., Living Room WiFi"
                  required
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="submit"
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition"
                >
                  Register
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="bg-slate-300 hover:bg-slate-400 text-slate-900 px-4 py-2 rounded-lg transition"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

      {loading ? (
        <p className="text-slate-600">Loading...</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents.length > 0 ? (
            agents.map((agent) => (
              <div key={agent.id} className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 bg-slate-100 rounded-lg">
                    <Server className="text-blue-600" size={24} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">{agent.name}</h3>
                    <span
                      className={`text-xs font-medium ${
                        agent.is_active ? 'text-green-600' : 'text-slate-400'
                      }`}
                    >
                      {agent.is_active ? '● Active' : '● Inactive'}
                    </span>
                  </div>
                </div>
                <div className="space-y-2 text-sm text-slate-600">
                  <p>
                    <span className="font-medium">Registered:</span>{' '}
                    {new Date(agent.created_at).toLocaleDateString()}
                  </p>
                  {agent.last_sync && (
                    <p>
                      <span className="font-medium">Last Sync:</span>{' '}
                      {new Date(agent.last_sync).toLocaleString()}
                    </p>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-full bg-white rounded-lg shadow p-12 text-center">
              <p className="text-slate-600 text-lg">No agents registered yet</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
