import { Shield, AlertTriangle, AlertCircle } from "lucide-react";
import Link from "next/link";

interface AuditStatsCardProps {
  last24h: number;
  critical: number;
  warnings: number;
}

export function AuditStatsCard({ last24h, critical, warnings }: AuditStatsCardProps) {
  const hasCritical = critical > 0;
  const hasWarnings = warnings > 0;

  return (
    <Link href="/admin/audit-logs" className="block">
      <div className="bg-gradient-to-br from-purple-900/50 to-pink-900/50 backdrop-blur-sm rounded-xl p-6 border border-purple-700/50 hover:border-purple-600/70 transition-all cursor-pointer">
        <div className="flex items-center justify-between mb-3">
          <span className="text-purple-300 text-sm font-medium">Audit Events (24h)</span>
          <Shield className="h-6 w-6 text-purple-400" />
        </div>
        <p className="text-4xl font-bold text-white mb-3">{last24h}</p>
        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-1">
            <AlertCircle className={`h-3 w-3 ${hasCritical ? 'text-red-400' : 'text-slate-600'}`} />
            <span className={hasCritical ? 'text-red-400' : 'text-slate-600'}>
              {critical} critical
            </span>
          </div>
          <div className="flex items-center gap-1">
            <AlertTriangle className={`h-3 w-3 ${hasWarnings ? 'text-yellow-400' : 'text-slate-600'}`} />
            <span className={hasWarnings ? 'text-yellow-400' : 'text-slate-600'}>
              {warnings} warnings
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}
