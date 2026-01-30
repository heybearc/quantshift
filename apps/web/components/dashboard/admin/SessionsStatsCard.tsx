import { Activity, TrendingUp, Clock } from "lucide-react";
import Link from "next/link";

interface SessionsStatsCardProps {
  current: number;
  peakToday: number;
  avgDuration: number;
}

export function SessionsStatsCard({ current, peakToday, avgDuration }: SessionsStatsCardProps) {
  return (
    <Link href="/admin/sessions" className="block">
      <div className="bg-gradient-to-br from-green-900/50 to-emerald-900/50 backdrop-blur-sm rounded-xl p-6 border border-green-700/50 hover:border-green-600/70 transition-all cursor-pointer">
        <div className="flex items-center justify-between mb-3">
          <span className="text-green-300 text-sm font-medium">Active Sessions</span>
          <Activity className="h-6 w-6 text-green-400" />
        </div>
        <p className="text-4xl font-bold text-white mb-3">{current}</p>
        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-1">
            <TrendingUp className="h-3 w-3 text-green-400" />
            <span className="text-green-400">Peak: {peakToday}</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3 text-slate-400" />
            <span className="text-slate-400">Avg: {avgDuration}m</span>
          </div>
        </div>
      </div>
    </Link>
  );
}
