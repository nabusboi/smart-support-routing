import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Users, User, Clock, TrendingUp, ArrowRight } from 'lucide-react';

const API_BASE = 'http://localhost:8001';

function AgentPanel({ agents: propAgents, apiConnected }) {
  const [agents, setAgents] = useState(propAgents || []);
  const [showRegister, setShowRegister] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState([]);
  const [totalAssignments, setTotalAssignments] = useState(0);
  const [newAgent, setNewAgent] = useState({ name: '', skills: { billing: 0.5, technical: 0.5, legal: 0.5 }, capacity: 5 });

  // Fetch routing history
  const fetchHistory = async () => {
    if (!apiConnected) return;
    try {
      const response = await axios.get(`${API_BASE}/api/agents/history?limit=20`);
      setHistory(response.data.history || []);
      setTotalAssignments(response.data.total_assignments || 0);
    } catch (err) {
      console.error('Error fetching history:', err);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [apiConnected]);

  // Use prop agents if API is not connected
  useEffect(() => {
    if (!apiConnected) {
      setAgents([
        { agent_id: '1', name: 'Agent Alpha', skills: { billing: 0.9, technical: 0.7, legal: 0.3 }, capacity: 5, current_load: 2, status: 'available' },
        { agent_id: '2', name: 'Agent Beta', skills: { billing: 0.4, technical: 0.95, legal: 0.6 }, capacity: 5, current_load: 3, status: 'available' },
        { agent_id: '3', name: 'Agent Gamma', skills: { billing: 0.3, technical: 0.5, legal: 0.98 }, capacity: 5, current_load: 1, status: 'available' },
      ]);
    } else {
      setAgents(propAgents || []);
    }
  }, [apiConnected, propAgents]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'available': return 'bg-green-500/20 text-green-400';
      case 'busy': return 'bg-yellow-500/20 text-yellow-400';
      case 'offline': return 'bg-red-500/20 text-red-400';
      default: return 'bg-gray-500/20 text-gray-400';
    }
  };

  const getSkillBarColor = (skill) => {
    if (skill >= 0.8) return 'bg-accent-500';
    if (skill >= 0.5) return 'bg-yellow-500';
    return 'bg-gray-500';
  };

  return (
    <div className="glass-card p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Users className="text-accent-400" />
          Agent Panel
        </h2>
        <div className="flex gap-2">
          {apiConnected && (
            <button
              onClick={() => { setShowHistory(!showHistory); fetchHistory(); }}
              className={`px-3 py-1 rounded-lg text-sm ${showHistory ? 'bg-accent-600' : 'bg-dark-700 hover:bg-dark-600'}`}
            >
              <TrendingUp size={14} className="inline mr-1" />
              Routing History
            </button>
          )}
          {apiConnected && (
            <button
              onClick={() => setShowRegister(!showRegister)}
              className="px-3 py-1 bg-accent-600 hover:bg-accent-500 rounded-lg text-sm"
            >
              {showRegister ? 'Cancel' : 'Register Agent'}
            </button>
          )}
        </div>
      </div>

      {/* Routing History */}
      {showHistory && (
        <div className="mb-6 p-4 bg-dark-700/50 rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium flex items-center gap-2">
              <Clock size={16} className="text-gray-400" />
              Routing History
            </h3>
            <span className="text-xs text-gray-400">Total: {totalAssignments} assignments</span>
          </div>
          {history.length === 0 ? (
            <div className="text-center py-4 text-gray-400 text-sm">
              No routing history yet. Tickets will be assigned to agents automatically.
            </div>
          ) : (
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {history.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 bg-dark-600/50 rounded text-xs">
                  <div className="flex items-center gap-2">
                    <span className="text-accent-400 font-mono">{item.ticket_id}</span>
                    <ArrowRight size={12} className="text-gray-500" />
                    <span className="text-green-400">{item.agent_name}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-gray-500">Score: {item.score?.toFixed(2)}</span>
                    <span className="text-gray-500">{new Date(item.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Register New Agent Form */}
      {showRegister && (
        <div className="mb-6 p-4 bg-dark-700/50 rounded-lg">
          <h3 className="font-medium mb-3">Register New Agent</h3>
          <div className="space-y-3">
            <input
              type="text"
              placeholder="Agent Name"
              value={newAgent.name}
              onChange={(e) => setNewAgent({ ...newAgent, name: e.target.value })}
              className="w-full bg-dark-600 border border-dark-500 rounded px-3 py-2 text-white text-sm"
            />
            <div className="flex gap-2">
              {Object.entries(newAgent.skills).map(([skill, value]) => (
                <div key={skill} className="flex-1">
                  <label className="text-xs text-gray-400 capitalize">{skill}</label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={value}
                    onChange={(e) => setNewAgent({
                      ...newAgent,
                      skills: { ...newAgent.skills, [skill]: parseFloat(e.target.value) }
                    })}
                    className="w-full"
                  />
                  <span className="text-xs text-gray-400">{(value * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
            <button
              onClick={async () => {
                try {
                  await axios.post(`${API_BASE}/api/agents/register`, {
                    name: newAgent.name,
                    skills: newAgent.skills,
                    capacity: newAgent.capacity
                  }, {
                    headers: {
                      'Content-Type': 'application/json'
                    }
                  });
                  setShowRegister(false);
                  setNewAgent({ name: '', skills: { billing: 0.5, technical: 0.5, legal: 0.5 }, capacity: 5 });
                } catch (err) {
                  console.error('Error registering agent:', err);
                }
              }}
              className="w-full py-2 bg-accent-600 hover:bg-accent-500 rounded text-sm"
            >
              Register
            </button>
          </div>
        </div>
      )}

      {/* Agents List */}
      <div className="space-y-4">
        {agents.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <User size={40} className="mx-auto mb-2 opacity-50" />
            <p>No agents registered yet</p>
          </div>
        ) : (
          agents.map((agent) => (
            <div key={agent.agent_id} className="p-4 bg-dark-700/50 rounded-lg">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="font-medium text-white flex items-center gap-2">
                    <User size={16} className="text-gray-400" />
                    {agent.name}
                  </h3>
                  <span className={`text-xs px-2 py-0.5 rounded ${getStatusColor(agent.status)}`}>
                    {agent.status}
                  </span>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-400">Load</div>
                  <div className="font-medium">
                    <span className="text-accent-400">{agent.current_load}</span>
                    <span className="text-gray-500">/{agent.capacity}</span>
                  </div>
                </div>
              </div>

              {/* Skills */}
              <div className="space-y-2">
                <div className="text-xs text-gray-400 mb-1">Skills</div>
                {Object.entries(agent.skills || {}).map(([skill, value]) => (
                  <div key={skill} className="flex items-center gap-2">
                    <span className="text-xs text-gray-400 capitalize w-16">{skill}</span>
                    <div className="flex-1 h-2 bg-dark-600 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${getSkillBarColor(value)}`}
                        style={{ width: `${(value || 0) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-400 w-8">{((value || 0) * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default AgentPanel;
