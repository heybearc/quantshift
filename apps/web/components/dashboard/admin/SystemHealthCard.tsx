import { Heart, Clock } from "lucide-react";
import Link from "next/link";

interface SystemHealthCardProps {
  status: 'healthy' | 'degraded' | 'down';
  uptime: number;
}

function formatUptime(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const days = Math.floor(hours / 24);
  if (days > 0) return `${days}d ${hours % 24}h`;
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

export function SystemHealthCard({ status, uptime }: SystemHealthCardProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'healthy':
        return 'text-green-400';
      case 'degraded':
        return 'text-yellow-400';
      case 'down':
        return 'text-red-400';
      default:
        return 'text-slate-400';
    }
  };

  const getStatusBg = () => {
    switch (status) {
      case 'healthy':
        return 'from-green-900/50 to-emerald-900/50 border-green-700/50 hover:border-green-600/70';
      case 'degraded':
        return 'from-yellow-900/50 to-orange-900/50 border-yellow-700/50 hover:border-yellow-600/70';
      case 'down':
        return 'from-red-900/50 to-orange-900/50 border-red-700/50 hover:border-red-600/70';
      default:
        return 'from-slate-800/50 to-slate-900/50 border-slate-700';
    }
  };

  return (
    <Link href="/admin/health" className="block">
      <div className={`bg-gradient-to-br ${getStatusBg()} backdrop-blur-sm rounded-xl p-6 border transition-all cursor-pointer`}>
        <div className="flex items-center justify-between mb-3">
          <span className="text-slate-300 text-sm font-medium">System Health</span>
          <Heart className={`h-6 w-6 ${getStatusColor()}`} />
        </div>
        <p className={`text-3xl font-bold mb-3 capitalize ${getStatusColor()}`}>
          {status}
        </p>
        <div className="flex items-center gap-1 text-xs">
          <Clock className="h-3 w-3 text-cyan-400" />
          <span className="text-slate-400">Web up {formatUptime(uptime)}</span>
        </div>
      </div>
    </Link>
  );
}
