import React from 'react';
import { Activity, Server, Zap, AlertTriangle, CheckCircle, XCircle, Package, Clock, Archive, Ban } from 'lucide-react';

function QueueMonitor({ queueSize, health, circuitBreakerStatus, onToggleCircuitBreaker, apiConnected, brokerStats }) {
  const isHealthy = health?.status === 'healthy';
  
  return (
    <div className="glass-card p-6">
      <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
        <Activity className="text-accent-400" />
        System Status
      </h2>

      {/* Health Status */}
      <div className="space-y-4">
        {/* API Status */}
        <div className="flex items-center justify-between p-3 bg-dark-700/50 rounded-lg">
          <div className="flex items-center gap-3">
            <Server className="text-gray-400" size={20} />
            <div>
              <div className="text-sm font-medium text-white">API Server</div>
              <div className="text-xs text-gray-400">FastAPI Backend</div>
            </div>
          </div>
          <div className={`flex items-center gap-1 ${apiConnected ? 'text-green-400' : 'text-red-400'}`}>
            {apiConnected ? <CheckCircle size={16} /> : <XCircle size={16} />}
            <span className="text-sm font-medium">{apiConnected ? 'Online' : 'Offline'}</span>
          </div>
        </div>

        {/* Queue Status */}
        <div className="flex items-center justify-between p-3 bg-dark-700/50 rounded-lg">
          <div className="flex items-center gap-3">
            <Activity className="text-gray-400" size={20} />
            <div>
              <div className="text-sm font-medium text-white">Queue Size</div>
              <div className="text-xs text-gray-400">Pending tickets</div>
            </div>
          </div>
          <div className="text-2xl font-bold text-accent-400">{queueSize}</div>
        </div>

        {/* Broker Queue Details */}
        {brokerStats && (
          <div className="p-3 bg-dark-700/50 rounded-lg space-y-2">
            <div className="flex items-center gap-2 mb-2">
              <Package className="text-gray-400" size={16} />
              <div className="text-sm font-medium text-white">Queue Details</div>
            </div>
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="flex items-center justify-center gap-1 p-2 bg-dark-600/50 rounded">
                <Clock size={14} className="text-yellow-400" />
                <span className="text-gray-400">Processing:</span>
                <span className="text-yellow-400 font-medium">{brokerStats.processing_count || 0}</span>
              </div>
              <div className="flex items-center justify-center gap-1 p-2 bg-dark-600/50 rounded">
                <CheckCircle size={14} className="text-green-400" />
                <span className="text-gray-400">Completed:</span>
                <span className="text-green-400 font-medium">{brokerStats.completed_count || 0}</span>
              </div>
              <div className="flex items-center justify-center gap-1 p-2 bg-dark-600/50 rounded">
                <Ban size={14} className="text-red-400" />
                <span className="text-gray-400">Dead Letter:</span>
                <span className="text-red-400 font-medium">{brokerStats.dead_letter_count || 0}</span>
              </div>
            </div>
            {!brokerStats.connected && (
              <div className="text-xs text-yellow-400 flex items-center gap-1">
                <AlertTriangle size={12} />
                Redis not connected - using in-memory queue
              </div>
            )}
          </div>
        )}

        {/* Circuit Breaker */}
        <div className="flex items-center justify-between p-3 bg-dark-700/50 rounded-lg">
          <div className="flex items-center gap-3">
            <Zap className="text-gray-400" size={20} />
            <div>
              <div className="text-sm font-medium text-white">Circuit Breaker</div>
              <div className="text-xs text-gray-400">ML Model Fallback</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`px-2 py-1 rounded text-xs font-medium ${
              circuitBreakerStatus === 'CLOSED' 
                ? 'bg-green-500/20 text-green-400' 
                : circuitBreakerStatus === 'HALF_OPEN'
                ? 'bg-yellow-500/20 text-yellow-400'
                : 'bg-red-500/20 text-red-400'
            }`}>
              {circuitBreakerStatus}
            </span>
            <button
              onClick={onToggleCircuitBreaker}
              disabled={!apiConnected}
              className={`text-xs px-2 py-1 rounded ${
                apiConnected 
                  ? 'bg-dark-600 hover:bg-dark-500 text-gray-300' 
                  : 'bg-dark-700 text-gray-500 cursor-not-allowed'
              }`}
            >
              Toggle
            </button>
          </div>
        </div>

        {/* ML Models Status */}
        <div className="p-3 bg-dark-700/50 rounded-lg">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="text-gray-400" size={16} />
            <div className="text-sm font-medium text-white">ML Models</div>
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Transformer (DistilBERT)</span>
              <span className={`px-2 py-0.5 rounded ${
                circuitBreakerStatus === 'CLOSED'
                  ? 'bg-green-500/20 text-green-400'
                  : 'bg-yellow-500/20 text-yellow-400'
              }`}>
                {circuitBreakerStatus === 'CLOSED' ? 'Active' : 'Fallback'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Baseline Classifier</span>
              <span className="px-2 py-0.5 rounded bg-green-500/20 text-green-400">Ready</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Embeddings (MiniLM)</span>
              <span className="px-2 py-0.5 rounded bg-green-500/20 text-green-400">Loaded</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default QueueMonitor;
