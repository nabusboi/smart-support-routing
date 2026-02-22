import React, { useState } from 'react';
import { Search, Filter, Clock, AlertTriangle, CheckCircle, XCircle, Zap, Pause, Activity } from 'lucide-react';

function TicketList({ tickets, onRefresh }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Filter tickets
  const filteredTickets = tickets.filter(ticket => {
    const matchesSearch =
      ticket.subject?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ticket.ticket_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ticket.customer_id?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || ticket.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <Zap className="text-green-400 animate-pulse" size={14} />;
      case 'paused': return <Pause className="text-amber-400" size={14} />;
      case 'completed': return <CheckCircle className="text-blue-400" size={14} />;
      case 'queued': return <Clock className="text-yellow-400" size={16} />;
      case 'processing': return <Activity className="text-accent-400" size={16} />;
      case 'cancelled': return <XCircle className="text-red-400" size={16} />;
      default: return <Clock className="text-gray-400" size={16} />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'paused': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      case 'completed': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'queued': return 'bg-yellow-500/20 text-yellow-400';
      case 'processing': return 'bg-accent-500/20 text-accent-400';
      case 'cancelled': return 'bg-red-500/20 text-red-400';
      default: return 'bg-gray-500/20 text-gray-400';
    }
  };

  const formatTime = (seconds) => {
    if (seconds === undefined || seconds === null) return '-';
    if (seconds <= 0) return '0s';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
  };

  const getUrgencyColor = (urgency) => {
    if (urgency >= 0.8) return 'bg-red-500';
    if (urgency >= 0.5) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getCategoryColor = (category) => {
    switch (category?.toLowerCase()) {
      case 'billing': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'technical': return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      case 'legal': return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  return (
    <div className="glass-card p-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Clock className="text-accent-400" />
          Live Ticket Queue ({filteredTickets.length})
        </h2>

        {/* Search & Filter */}
        <div className="flex gap-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:flex-initial">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input
              type="text"
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full sm:w-64 bg-dark-700/50 border border-dark-600 rounded-lg pl-10 pr-4 py-2 text-white text-sm placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-accent-500"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-dark-700/50 border border-dark-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-1 focus:ring-accent-500"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="queued">Queued</option>
            <option value="completed">Completed</option>
          </select>
        </div>
      </div>

      {/* Tickets Table */}
      <div className="overflow-x-auto scrollbar-thin">
        <table className="w-full">
          <thead>
            <tr className="text-left text-gray-400 text-xs uppercase tracking-wider border-b border-dark-700">
              <th className="pb-3 font-semibold">Ticket ID</th>
              <th className="pb-3 font-semibold">Subject & Customer</th>
              <th className="pb-3 font-semibold">Category</th>
              <th className="pb-3 font-semibold">Urgency</th>
              <th className="pb-3 font-semibold">Agent</th>
              <th className="pb-3 font-semibold">ETA</th>
              <th className="pb-3 font-semibold text-center">Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredTickets.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-12 text-center text-gray-500 italic">
                  No tickets found matching your search.
                </td>
              </tr>
            ) : (
              filteredTickets.map((ticket, index) => (
                <tr
                  key={ticket.ticket_id || index}
                  className="border-b border-dark-700/30 hover:bg-white/5 transition-colors group"
                >
                  <td className="py-4">
                    <span className="font-mono text-accent-400 text-xs">
                      {ticket.ticket_id}
                    </span>
                  </td>
                  <td className="py-4 pr-4">
                    <div className="text-sm font-medium text-white group-hover:text-accent-300 transition-colors truncate max-w-[200px]" title={ticket.subject}>
                      {ticket.subject}
                    </div>
                    <div className="text-[10px] text-gray-500 font-mono">
                      {ticket.customer_id}
                    </div>
                  </td>
                  <td className="py-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getCategoryColor(ticket.category)}`}>
                      {ticket.category || 'General'}
                    </span>
                  </td>
                  <td className="py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-12 h-1.5 bg-dark-700 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${getUrgencyColor(ticket.urgency)}`}
                          style={{ width: `${(ticket.urgency || 0) * 100}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-gray-400 tabular-nums">
                        {((ticket.urgency || 0) * 100).toFixed(0)}%
                      </span>
                    </div>
                  </td>
                  <td className="py-4">
                    <span className="text-sm text-gray-300">
                      {ticket.assigned_agent || <span className="text-gray-600 italic">Unassigned</span>}
                    </span>
                  </td>
                  <td className="py-4">
                    <div className={`text-sm font-mono tabular-nums ${ticket.ticket_status === 'active' ? 'text-accent-400 animate-pulse' : 'text-gray-500'
                      }`}>
                      {ticket.remaining_eta !== undefined ? formatTime(ticket.remaining_eta) : '-'}
                    </div>
                  </td>
                  <td className="py-4">
                    <div className="flex justify-center">
                      <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-[10px] font-bold border ${getStatusColor(ticket.ticket_status || ticket.status)}`}>
                        {getStatusIcon(ticket.ticket_status || ticket.status)}
                        {(ticket.ticket_status || ticket.status).toUpperCase()}
                      </span>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default TicketList;
