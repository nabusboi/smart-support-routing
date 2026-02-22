import React, { useState } from 'react';
import { Plus, Send, Loader2, CheckCircle, AlertCircle } from 'lucide-react';

function TicketForm({ onSubmit, apiConnected }) {
  const [formData, setFormData] = useState({
    subject: '',
    description: '',
    customer_id: ''
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await onSubmit(formData);
      setResult(response);
      setFormData({ subject: '', description: '', customer_id: '' });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create ticket');
    } finally {
      setLoading(false);
    }
  };

  const getUrgencyColor = (urgency) => {
    if (urgency >= 0.8) return 'text-red-400';
    if (urgency >= 0.5) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getCategoryColor = (category) => {
    switch (category?.toLowerCase()) {
      case 'billing': return 'bg-blue-500/20 text-blue-400';
      case 'technical': return 'bg-purple-500/20 text-purple-400';
      case 'legal': return 'bg-orange-500/20 text-orange-400';
      default: return 'bg-gray-500/20 text-gray-400';
    }
  };

  return (
    <div className="glass-card p-6">
      <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
        <Plus className="text-accent-400" />
        Create New Ticket
      </h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Subject */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Subject
          </label>
          <input
            type="text"
            value={formData.subject}
            onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
            className="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent-500"
            placeholder="e.g., Cannot access my account"
            required
          />
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Description
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            className="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent-500 h-24 resize-none"
            placeholder="Describe your issue in detail..."
            required
          />
        </div>

        {/* Customer ID */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Customer ID
          </label>
          <input
            type="text"
            value={formData.customer_id}
            onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
            className="w-full bg-dark-700 border border-dark-600 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent-500"
            placeholder="e.g., cust_123"
            required
          />
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading || !apiConnected}
          className={`w-full flex items-center justify-center gap-2 py-3 rounded-lg font-medium transition-all ${
            loading || !apiConnected
              ? 'bg-dark-600 text-gray-500 cursor-not-allowed'
              : 'bg-accent-600 hover:bg-accent-500 text-white shadow-lg shadow-accent-500/30 hover:shadow-accent-500/50'
          }`}
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" size={18} />
              Processing with ML...
            </>
          ) : (
            <>
              <Send size={18} />
              Submit Ticket
            </>
          )}
        </button>
      </form>

      {/* Result/Error Display */}
      {result && (
        <div className="mt-4 p-4 bg-green-500/20 border border-green-500/30 rounded-lg">
          <div className="flex items-center gap-2 text-green-400 mb-2">
            <CheckCircle size={18} />
            <span className="font-medium">Ticket Created!</span>
          </div>
          <div className="text-sm space-y-1">
            <div className="text-gray-300">
              ID: <span className="font-mono text-accent-400">{result.ticket_id}</span>
            </div>
            {result.category && (
              <div className="flex items-center gap-2">
                <span className="text-gray-400">Category:</span>
                <span className={`px-2 py-0.5 rounded text-xs ${getCategoryColor(result.category)}`}>
                  {result.category}
                </span>
              </div>
            )}
            {result.urgency !== undefined && result.urgency !== null && (
              <div className="flex items-center gap-2">
                <span className="text-gray-400">Urgency:</span>
                <span className={`font-medium ${getUrgencyColor(result.urgency)}`}>
                  {(result.urgency * 100).toFixed(0)}%
                </span>
              </div>
            )}
            <div className="text-gray-400 text-xs mt-1">{result.message}</div>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-4 p-4 bg-red-500/20 border border-red-500/30 rounded-lg">
          <div className="flex items-center gap-2 text-red-400">
            <AlertCircle size={18} />
            <span className="font-medium">Error</span>
          </div>
          <div className="text-sm text-gray-300 mt-1">{error}</div>
        </div>
      )}
    </div>
  );
}

export default TicketForm;
