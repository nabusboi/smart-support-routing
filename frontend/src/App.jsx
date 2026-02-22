import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  Ticket, Users, Activity, Zap, Brain,
} from 'lucide-react';

// Components
import Header from './components/Header';
import TicketForm from './components/TicketForm';
import TicketList from './components/TicketList';
import QueueMonitor from './components/QueueMonitor';
import AgentPanel from './components/AgentPanel';
import MLInsights from './components/MLInsights';
import StatsBar from './components/StatsBar';

const API_BASE = 'http://localhost:8001';

function App() {
  const [tickets, setTickets] = useState([]);
  const [queueSize, setQueueSize] = useState(0);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('tickets');
  const [mlInsights, setMlInsights] = useState(null);
  const [agents, setAgents] = useState([]);
  const [circuitBreakerStatus, setCircuitBreakerStatus] = useState('CLOSED');
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [apiConnected, setApiConnected] = useState(false);

  // New state for detailed stats
  const [brokerStats, setBrokerStats] = useState(null);
  const [circuitBreakerStats, setCircuitBreakerStats] = useState(null);
  const [preemptionStats, setPreemptionStats] = useState({ total_preemptions: 0, paused_tickets: 0 });

  // Fetch tickets from API
  const fetchTickets = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/tickets`);
      setTickets(response.data.tickets || []);
      setApiConnected(true);
    } catch (error) {
      console.error('Error fetching tickets:', error);
      setApiConnected(false);
    }
  }, []);

  // Fetch health/queue status
  const fetchHealth = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/health`);
      setHealth(response.data);
      setQueueSize(response.data.queue_size || 0);
      if (response.data.circuit_breaker) {
        setCircuitBreakerStatus(response.data.circuit_breaker);
      }
      setApiConnected(true);
    } catch (error) {
      console.error('Error fetching health:', error);
      setApiConnected(false);
      setHealth({ status: 'offline', queue_size: 0 });
    }
  }, []);

  // Fetch agents from API
  const fetchAgents = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/agents`);
      setAgents(response.data || []);
    } catch (error) {
      console.error('Error fetching agents:', error);
    }
  }, []);

  // Fetch ML status
  const fetchMLStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/ml/status`);
      if (response.data.circuit_breaker) {
        setCircuitBreakerStatus(response.data.circuit_breaker.state);
      }
      return response.data;
    } catch (error) {
      console.error('Error fetching ML status:', error);
      return null;
    }
  }, []);

  // Fetch stats
  const fetchStats = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/stats`);
      setPreemptionStats({
        total_preemptions: response.data.total_preemptions || 0,
        paused_tickets: response.data.paused || 0
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching stats:', error);
      return null;
    }
  }, []);

  // Fetch broker stats (new)
  const fetchBrokerStats = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/broker/stats`);
      setBrokerStats(response.data);
    } catch (error) {
      console.error('Error fetching broker stats:', error);
      setBrokerStats(null);
    }
  }, []);

  // Fetch circuit breaker detailed stats (new)
  const fetchCircuitBreakerStats = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/circuit-breaker/stats`);
      setCircuitBreakerStats(response.data);
    } catch (error) {
      console.error('Error fetching circuit breaker stats:', error);
      setCircuitBreakerStats(null);
    }
  }, []);

  // Refresh all data
  const refreshData = useCallback(async () => {
    setLoading(true);
    await Promise.all([fetchTickets(), fetchHealth(), fetchAgents()]);

    const [mlStatus, statsData, brokerStatsData, cbStats] = await Promise.all([
      fetchMLStatus(),
      fetchStats(),
      fetchBrokerStats(),
      fetchCircuitBreakerStats()
    ]);

    // Update ML insights with real data
    if (statsData) {
      const categories = ['Billing', 'Technical', 'Legal', 'General'];
      setMlInsights({
        lastAnalyzed: new Date().toISOString(),
        categories: categories.map(cat => ({
          name: cat,
          count: statsData.categories?.[cat] || 0
        })),
        avgUrgency: statsData.avg_urgency || 0,
        highUrgencyCount: statsData.high_urgency_count || 0,
        duplicateAlerts: 0,
        circuitBreaker: circuitBreakerStatus,
        mlStatus: mlStatus
      });
    }

    setLastUpdated(new Date());
    setLoading(false);
  }, [fetchTickets, fetchHealth, fetchAgents, fetchMLStatus, fetchStats, fetchBrokerStats, fetchCircuitBreakerStats, circuitBreakerStatus]);

  // Initial load
  useEffect(() => {
    refreshData();
    const interval = setInterval(refreshData, 5000);
    return () => clearInterval(interval);
  }, [refreshData]);

  // Handle ticket creation
  const handleTicketCreate = async (ticketData) => {
    try {
      const response = await axios.post(`${API_BASE}/api/tickets`, ticketData);
      await refreshData();
      return response.data;
    } catch (error) {
      console.error('Error creating ticket:', error);
      throw error;
    }
  };

  // Calculate stats from real ticket data
  const stats = {
    total: tickets.length,
    queued: tickets.filter(t => t.status === 'queued').length,
    processing: tickets.filter(t => t.ticket_status === 'active').length,
    paused: tickets.filter(t => t.ticket_status === 'paused').length,
    completed: tickets.filter(t => t.status === 'completed').length,
    highUrgency: tickets.filter(t => (t.urgency || 0) >= 0.8).length,
    preemptions: preemptionStats.total_preemptions
  };

  // Toggle circuit breaker via API
  const toggleCircuitBreaker = async () => {
    try {
      const response = await axios.post(`${API_BASE}/api/ml/circuit-breaker/toggle`);
      setCircuitBreakerStatus(response.data.state);
      // Also refresh circuit breaker stats
      fetchCircuitBreakerStats();
    } catch (error) {
      console.error('Error toggling circuit breaker:', error);
      // Fallback to local toggle for demo
      setCircuitBreakerStatus(prev => prev === 'CLOSED' ? 'OPEN' : 'CLOSED');
    }
  };

  return (
    <div className="min-h-screen bg-dark-900">
      {/* Header */}
      <Header
        lastUpdated={lastUpdated}
        onRefresh={refreshData}
        loading={loading}
        apiConnected={apiConnected}
      />

      {/* Stats Bar */}
      <StatsBar stats={stats} queueSize={queueSize} agentsCount={agents.length} />

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6 overflow-x-auto">
          {[
            { id: 'tickets', label: 'Tickets', icon: Ticket },
            { id: 'queue', label: 'Queue Monitor', icon: Activity },
            { id: 'agents', label: 'Agent Panel', icon: Users },
            { id: 'ml', label: 'ML Insights', icon: Brain },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${activeTab === tab.id
                ? 'bg-accent-600 text-white shadow-lg shadow-accent-500/30'
                : 'bg-dark-800 text-gray-400 hover:bg-dark-700 hover:text-gray-200'
                }`}
            >
              <tab.icon size={18} />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Ticket Form & Queue */}
          <div className="lg:col-span-1 space-y-6">
            <TicketForm onSubmit={handleTicketCreate} apiConnected={apiConnected} />
            <QueueMonitor
              queueSize={queueSize}
              health={health}
              circuitBreakerStatus={circuitBreakerStatus}
              onToggleCircuitBreaker={toggleCircuitBreaker}
              apiConnected={apiConnected}
              brokerStats={brokerStats}
            />
          </div>

          {/* Right Column - Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {activeTab === 'tickets' && (
              <TicketList
                tickets={tickets}
                onRefresh={refreshData}
              />
            )}
            {activeTab === 'agents' && (
              <AgentPanel agents={agents} apiConnected={apiConnected} onRefresh={fetchAgents} />
            )}
            {activeTab === 'ml' && (
              <MLInsights insights={mlInsights} apiConnected={apiConnected} circuitBreakerStats={circuitBreakerStats} />
            )}
            {activeTab === 'queue' && (
              <div className="glass-card p-6">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <Activity className="text-accent-400" />
                  Queue Details
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-dark-700/50 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-accent-400">{queueSize}</div>
                    <div className="text-sm text-gray-400">In Queue</div>
                  </div>
                  <div className="bg-dark-700/50 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-yellow-400">{stats.processing}</div>
                    <div className="text-sm text-gray-400">Processing</div>
                  </div>
                  <div className="bg-dark-700/50 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-green-400">{stats.completed}</div>
                    <div className="text-sm text-gray-400">Completed</div>
                  </div>
                  <div className="bg-dark-700/50 rounded-lg p-4 text-center">
                    <div className="text-3xl font-bold text-red-400">{stats.highUrgency}</div>
                    <div className="text-sm text-gray-400">High Urgency</div>
                  </div>
                </div>
                {/* Broker Details */}
                {brokerStats && (
                  <div className="mt-4 grid grid-cols-3 gap-4">
                    <div className="bg-dark-700/50 rounded-lg p-3 text-center">
                      <div className="text-2xl font-bold text-yellow-400">{brokerStats.processing_count || 0}</div>
                      <div className="text-xs text-gray-400">Processing</div>
                    </div>
                    <div className="bg-dark-700/50 rounded-lg p-3 text-center">
                      <div className="text-2xl font-bold text-green-400">{brokerStats.completed_count || 0}</div>
                      <div className="text-xs text-gray-400">Completed</div>
                    </div>
                    <div className="bg-dark-700/50 rounded-lg p-3 text-center">
                      <div className="text-2xl font-bold text-red-400">{brokerStats.dead_letter_count || 0}</div>
                      <div className="text-xs text-gray-400">Dead Letter</div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
