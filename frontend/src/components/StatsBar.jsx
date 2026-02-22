import React from 'react';
import { Ticket, Users, Activity, Zap, AlertTriangle, Pause, CheckCircle2, Repeat } from 'lucide-react';

function StatsBar({ stats, queueSize, agentsCount }) {
  const statItems = [
    {
      label: 'Total Tickets',
      value: stats.total,
      icon: Ticket,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10'
    },
    {
      label: 'In Queue',
      value: queueSize,
      icon: Activity,
      color: 'text-yellow-400',
      bg: 'bg-yellow-500/10'
    },
    {
      label: 'Active',
      value: stats.processing,
      icon: Zap,
      color: 'text-green-400',
      bg: 'bg-green-500/10'
    },
    {
      label: 'Paused',
      value: stats.paused,
      icon: Pause,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10'
    },
    {
      label: 'Completed',
      value: stats.completed,
      icon: CheckCircle2,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10'
    },
    {
      label: 'Preemptions',
      value: stats.preemptions,
      icon: Repeat,
      color: 'text-purple-400',
      bg: 'bg-purple-500/10'
    },
    {
      label: 'Active Agents',
      value: agentsCount,
      icon: Users,
      color: 'text-cyan-400',
      bg: 'bg-cyan-500/10'
    },
    {
      label: 'High Urgency',
      value: stats.highUrgency,
      icon: AlertTriangle,
      color: 'text-red-400',
      bg: 'bg-red-500/10'
    },
  ];

  return (
    <div className="bg-dark-800/50 border-b border-dark-700">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center gap-4 overflow-x-auto scrollbar-thin">
          {statItems.map((item, index) => (
            <div
              key={index}
              className={`flex items-center gap-3 px-4 py-2 rounded-lg ${item.bg} min-w-fit`}
            >
              <item.icon className={item.color} size={20} />
              <div>
                <div className={`text-xl font-bold ${item.color}`}>
                  {item.value}
                </div>
                <div className="text-xs text-gray-400">{item.label}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default StatsBar;
