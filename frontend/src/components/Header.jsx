import React from 'react';
import { Zap, RefreshCw, Clock, Wifi, WifiOff } from 'lucide-react';

function Header({ lastUpdated, onRefresh, loading, apiConnected }) {
  const formatTime = (date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }).format(date);
  };

  return (
    <header className="bg-dark-800 border-b border-dark-700 sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-12 h-12 bg-gradient-to-br from-accent-500 to-accent-700 rounded-xl flex items-center justify-center shadow-lg shadow-accent-500/30">
                <Zap className="text-white" size={24} />
              </div>
              <div className={`absolute -top-1 -right-1 w-3 h-3 rounded-full ${apiConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                Smart-Support
              </h1>
              <p className="text-xs text-gray-400">AI-Powered Ticket Routing Engine</p>
            </div>
          </div>

          {/* Status & Actions */}
          <div className="flex items-center gap-4">
            {/* API Connection Status */}
            <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
              apiConnected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
            }`}>
              {apiConnected ? <Wifi size={14} /> : <WifiOff size={14} />}
              <span className="hidden sm:inline">{apiConnected ? 'Connected' : 'Offline'}</span>
            </div>

            {/* Last Updated */}
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <Clock size={14} />
              <span>Updated: {formatTime(lastUpdated)}</span>
            </div>

            {/* Refresh Button */}
            <button
              onClick={onRefresh}
              disabled={loading}
              className={`flex items-center gap-2 px-4 py-2 bg-dark-700 hover:bg-dark-600 rounded-lg transition-all ${
                loading ? 'opacity-50 cursor-not-allowed' : 'hover:shadow-lg'
              }`}
            >
              <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
              <span className="hidden sm:inline">Refresh</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
