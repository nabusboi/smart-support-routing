import React, { useState } from 'react';
import { Search, Filter, Clock, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

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
      case 'queued': return <Clock className="text-yellow-400" size={16} />;
      case 'processing': return <AlertTriangle className="text-blue-400" size={16} />;
      case 'completed': return <CheckCircle className="text-green-400" size={16} />;
      case 'cancelled': return <XCircle className="text-red-400" size={16} />;
      default: return <Clock className="text-gray-400" size={16} />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'queued': return 'bg-yellow-500/20 text-yellow-400';
      case 'processing': return 'bg-blue-500/20 text-blue-400';
      case 'completed': return 'bg-green-500/20 text-green-400';
      case 'cancelled': return 'bg-red-500/20 text-red-400';
      default: return 'bg-gray-500/20 text-gray-400';
    }
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
          <Search className="text-accent-400" />
          Tickets ({filteredTickets.length})
        </h2>

        {/* Search & Filter */}
        <div className="flex gap-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:flex-initial">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input
              type="text"
              placeholder="Search tickets..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full sm:w-64 bg-dark-700 border border-dark-600 rounded-lg pl-10 pr-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent-500"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-accent-500"
          >
            <option value="all">All Status</option>
            <option value="queued">Queued</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Tickets Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="text-left text-gray-400 text-sm border-b border-dark-700">
              <th className="pb-3 font-medium">Ticket ID</th>
              <th className="pb-3 font-medium">Subject</th>
              <th className="pb-3 font-medium">Category</th>
              <th className="pb-3 font-medium">Urgency</th>
              <th className="pb-3 font-medium">Status</th>
              <th className="pb-3 font-medium">Created</th>
            </tr>
          </thead>
          <tbody>
            {filteredTickets.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-gray-400">
                  No tickets found. Create your first ticket!
                </td>
              </tr>
            ) : (
              filteredTickets.map((ticket, index) => (
                <tr 
                  key={ticket.ticket_id || index} 
                  className="border-b border-dark-700/50 hover:bg-dark-700/30 transition-colors"
                >
                  <td className="py-3">
                    <span className="font-mono text-accent-400 text-sm">
                      {ticket.ticket_id}
                    </span>
                  </td>
                  <td className="py-3 max-w-xs">
                    <div className="truncate text-white" title={ticket.subject}>
                      {ticket.subject}
                    </div>
                    <div className="text-xs text-gray-500 truncate">
                      {ticket.customer_id}
                    </div>
                  </td>
                  <td className="py-3">
                    {ticket.category ? (
                      <span className={`px-2 py-1 rounded text-xs border ${getCategoryColor(ticket.category)}`}>
                        {ticket.category}
                      </span>
                    ) : (
                      <span className="text-gray-500 text-xs">-</span>
                    )}
                  </td>
                  <td className="py-3">
                    {ticket.urgency !== undefined && ticket.urgency !== null ? (
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-dark-600 rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${getUrgencyColor(ticket.urgency)}`}
                            style={{ width: `${ticket.urgency * 100}%` }}
                          />
                        </div>
                        <span className={`text-xs font-medium ${
                          ticket.urgency >= 0.8 ? 'text-red-400' : 
                          ticket.urgency >= 0.5 ? 'text-yellow-400' : 'text-green-400'
                        }`}>
                          {(ticket.urgency * 100).toFixed(0)}%
                        </span>
                      </div>
                    ) : (
                      <span className="text-gray-500 text-xs">-</span>
                    )}
                  </td>
                  <td className="py-3">
                    <span className={`flex items-center gap-1 px-2 py-1 rounded text-xs ${getStatusColor(ticket.status)}`}>
                      {getStatusIcon(ticket.status)}
                      {ticket.status}
                    </span>
                  </td>
                  <td className="py-3 text-gray-400 text-sm">
                    {ticket.created_at ? new Date(ticket.created_at).toLocaleDateString() : '-'}
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
