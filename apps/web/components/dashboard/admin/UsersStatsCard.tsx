import { Users, UserCheck, UserPlus, UserX } from "lucide-react";
import Link from "next/link";

interface UsersStatsCardProps {
  total: number;
  active: number;
  pending: number;
  inactive: number;
}

export function UsersStatsCard({ total, active, pending, inactive }: UsersStatsCardProps) {
  return (
    <Link href="/users" className="block">
      <div className="bg-gradient-to-br from-blue-900/50 to-indigo-900/50 backdrop-blur-sm rounded-xl p-6 border border-blue-700/50 hover:border-blue-600/70 transition-all cursor-pointer">
        <div className="flex items-center justify-between mb-3">
          <span className="text-blue-300 text-sm font-medium">Total Users</span>
          <Users className="h-6 w-6 text-blue-400" />
        </div>
        <p className="text-4xl font-bold text-white mb-3">{total}</p>
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="flex items-center gap-1">
            <UserCheck className="h-3 w-3 text-green-400" />
            <span className="text-green-400">{active} active</span>
          </div>
          <div className="flex items-center gap-1">
            <UserPlus className="h-3 w-3 text-yellow-400" />
            <span className="text-yellow-400">{pending} pending</span>
          </div>
          <div className="flex items-center gap-1">
            <UserX className="h-3 w-3 text-slate-400" />
            <span className="text-slate-400">{inactive} inactive</span>
          </div>
        </div>
      </div>
    </Link>
  );
}
