import React from 'react';
import { Brain, Zap, AlertTriangle, CheckCircle, BarChart3, Cpu, Activity, Clock, Target } from 'lucide-react';

function MLInsights({ insights, apiConnected, circuitBreakerStats }) {
  if (!insights) {
    return (
      <div className="glass-card p-6">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Brain className="text-accent-400" />
          ML Insights
        </h2>
        <div className="text-center py-8 text-gray-400">
          <Brain size={40} className="mx-auto mb-2 opacity-50" />
          <p>No ML insights available yet</p>
          <p className="text-sm">Create tickets to see AI classification results</p>
        </div>
      </div>
    );
  }

  const getCategoryColor = (name) => {
    switch (name?.toLowerCase()) {
      case 'billing': return 'bg-blue-500';
      case 'technical': return 'bg-purple-500';
      case 'legal': return 'bg-orange-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="glass-card p-6">
      <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
        <Brain className="text-accent-400" />
        ML Insights
        {!apiConnected && (
          <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded">
            Demo Mode
          </span>
        )}
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Category Distribution */}
        <div className="p-4 bg-dark-700/50 rounded-lg">
          <h3 className="font-medium mb-4 flex items-center gap-2">
            <BarChart3 className="text-gray-400" size={18} />
            Category Distribution
          </h3>
          <div className="space-y-3">
            {insights.categories?.map((cat, idx) => (
              <div key={idx} className="flex items-center gap-3">
                <div className="w-20 text-sm text-gray-400">{cat.name}</div>
                <div className="flex-1 h-4 bg-dark-600 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${getCategoryColor(cat.name)}`}
                    style={{ 
                      width: `${insights.total ? (cat.count / insights.total) * 100 : 0}%` 
                    }}
                  />
                </div>
                <div className="w-8 text-sm text-gray-400 text-right">{cat.count}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Urgency Stats */}
        <div className="p-4 bg-dark-700/50 rounded-lg">
          <h3 className="font-medium mb-4 flex items-center gap-2">
            <AlertTriangle className="text-gray-400" size={18} />
            Urgency Analysis
          </h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-400">Average Urgency</span>
                <span className={`font-medium ${
                  (insights.avgUrgency || 0) >= 0.8 ? 'text-red-400' :
                  (insights.avgUrgency || 0) >= 0.5 ? 'text-yellow-400' : 'text-green-400'
                }`}>
                  {((insights.avgUrgency || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div className="h-2 bg-dark-600 rounded-full overflow-hidden">
                <div 
                  className={`h-full ${
                    (insights.avgUrgency || 0) >= 0.8 ? 'bg-red-500' :
                    (insights.avgUrgency || 0) >= 0.5 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${(insights.avgUrgency || 0) * 100}%` }}
                />
              </div>
            </div>
            <div className="flex items-center justify-between p-3 bg-dark-600/50 rounded-lg">
              <div className="text-sm text-gray-400">High Urgency Tickets</div>
              <div className="text-xl font-bold text-red-400">
                {insights.highUrgencyCount || 0}
              </div>
            </div>
          </div>
        </div>

        {/* Model Status */}
        <div className="p-4 bg-dark-700/50 rounded-lg">
          <h3 className="font-medium mb-4 flex items-center gap-2">
            <Cpu className="text-gray-400" size={18} />
            ML Model Status
          </h3>
          <div className="space-y-3 text-sm">
            {insights.mlStatus && (
              <>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Transformer</span>
                  <span className={`px-2 py-0.5 rounded ${
                    insights.mlStatus.transformer_model?.status === 'loaded'
                      ? 'bg-green-500/20 text-green-400'
                      : 'bg-yellow-500/20 text-yellow-400'
                  }`}>
                    {insights.mlStatus.transformer_model?.status || 'unknown'}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Latency</span>
                  <span className="text-white">
                    {insights.mlStatus.transformer_model?.latency_ms || 'N/A'}ms
                  </span>
                </div>
              </>
            )}
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Baseline</span>
              <span className="px-2 py-0.5 rounded bg-green-500/20 text-green-400">Ready</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Embeddings</span>
              <span className="px-2 py-0.5 rounded bg-green-500/20 text-green-400">Loaded</span>
            </div>
          </div>
        </div>

        {/* Circuit Breaker Detailed */}
        <div className="p-4 bg-dark-700/50 rounded-lg">
          <h3 className="font-medium mb-4 flex items-center gap-2">
            <Zap className="text-gray-400" size={18} />
            Circuit Breaker Details
          </h3>
          <div className="space-y-3">
            {/* State */}
            <div className="flex items-center justify-between p-3 bg-dark-600/50 rounded-lg">
              <div>
                <div className="text-sm text-gray-400">Current State</div>
                <div className={`text-lg font-medium ${
                  insights.circuitBreaker === 'CLOSED' ? 'text-green-400' : 
                  insights.circuitBreaker === 'HALF_OPEN' ? 'text-yellow-400' : 'text-red-400'
                }`}>
                  {insights.circuitBreaker || 'CLOSED'}
                </div>
              </div>
              <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                insights.circuitBreaker === 'CLOSED' 
                  ? 'bg-green-500/20' 
                  : insights.circuitBreaker === 'HALF_OPEN'
                  ? 'bg-yellow-500/20'
                  : 'bg-red-500/20'
              }`}>
                {insights.circuitBreaker === 'CLOSED' ? (
                  <CheckCircle className="text-green-400" size={24} />
                ) : insights.circuitBreaker === 'HALF_OPEN' ? (
                  <Activity className="text-yellow-400" size={24} />
                ) : (
                  <AlertTriangle className="text-red-400" size={24} />
                )}
              </div>
            </div>
            
            {/* Detailed Stats from API */}
            {circuitBreakerStats && (
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 bg-dark-600/50 rounded flex items-center justify-between">
                  <span className="text-gray-400">Failures</span>
                  <span className="text-red-400 font-medium">{circuitBreakerStats.failure_count || 0}</span>
                </div>
                <div className="p-2 bg-dark-600/50 rounded flex items-center justify-between">
                  <span className="text-gray-400">Successes</span>
                  <span className="text-green-400 font-medium">{circuitBreakerStats.success_count || 0}</span>
                </div>
                <div className="p-2 bg-dark-600/50 rounded flex items-center justify-between">
                  <span className="text-gray-400">Avg Latency</span>
                  <span className={`font-medium ${
                    (circuitBreakerStats.average_latency_ms || 0) > 500 ? 'text-red-400' : 'text-white'
                  }`}>
                    {circuitBreakerStats.average_latency_ms || 0}ms
                  </span>
                </div>
                <div className="p-2 bg-dark-600/50 rounded flex items-center justify-between">
                  <span className="text-gray-400">Threshold</span>
                  <span className="text-white">{circuitBreakerStats.latency_threshold_ms || 500}ms</span>
                </div>
                {circuitBreakerStats.time_until_reset_seconds > 0 && (
                  <div className="col-span-2 p-2 bg-dark-600/50 rounded flex items-center justify-between">
                    <span className="text-gray-400 flex items-center gap-1">
                      <Clock size={12} /> Reset in
                    </span>
                    <span className="text-yellow-400 font-medium">{circuitBreakerStats.time_until_reset_seconds}s</span>
                  </div>
                )}
              </div>
            )}
            
            <p className="text-xs text-gray-500">
              When latency exceeds 500ms or 5+ failures occur, the system automatically falls back to the baseline classifier.
            </p>
          </div>
        </div>
      </div>

      {/* Last Analyzed */}
      {insights.lastAnalyzed && (
        <div className="mt-4 text-xs text-gray-500 text-center">
          Last analyzed: {new Date(insights.lastAnalyzed).toLocaleString()}
        </div>
      )}
    </div>
  );
}

export default MLInsights;
