"use client";

import { useAuth } from "@/lib/auth-context";
import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";
import { 
  LayoutDashboard, 
  TrendingUp, 
  Activity, 
  BarChart3, 
  Mail, 
  Users, 
  Settings,
  FileText,
  Shield,
  Zap,
  BookOpen,
  LogOut,
  Menu,
  X,
  UserPlus,
  UserCheck
} from "lucide-react";
import { useState } from "react";
import { APP_VERSION, APP_NAME } from "@/lib/version";

export function Navigation() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const platformNav = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Trades", href: "/trades", icon: TrendingUp },
    { name: "Positions", href: "/positions", icon: Activity },
    { name: "Performance", href: "/performance", icon: BarChart3 },
    { name: "Email Notifications", href: "/settings/notifications", icon: Mail },
    { name: "Help", href: "/help", icon: BookOpen },
  ];

  const adminNav = [
    { name: "User Management", href: "/users", icon: Users },
    { name: "Pending Approvals", href: "/admin/pending-users", icon: UserCheck },
    { name: "User Invitations", href: "/admin/invitations", icon: UserPlus },
    { name: "Session Management", href: "/admin/sessions", icon: Shield },
    { name: "Audit Logs", href: "/admin/audit-logs", icon: FileText },
    { name: "Health Monitor", href: "/admin/health", icon: Activity },
    { name: "API Status", href: "/admin/api-status", icon: Zap },
    { name: "Platform Settings", href: "/admin/settings", icon: Settings },
  ];

  const handleLogout = async () => {
    await logout();
    window.location.href = "/login";
  };

  return (
    <>
      {/* Mobile menu button */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 rounded-md bg-white shadow-lg text-gray-600 hover:text-gray-900"
        >
          {mobileMenuOpen ? (
            <X className="h-6 w-6" />
          ) : (
            <Menu className="h-6 w-6" />
          )}
        </button>
      </div>

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-40 w-64 bg-slate-900 border-r border-slate-800 transform transition-transform duration-300 ease-in-out
        lg:translate-x-0 ${mobileMenuOpen ? "translate-x-0" : "-translate-x-full"}
      `}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-center h-24 px-6 bg-slate-900 border-b border-slate-800">
            <div className="flex flex-col items-center gap-2">
              <Image
                src="/logo.svg"
                alt="QuantShift Logo"
                width={60}
                height={60}
                className="rounded-lg"
              />
              <div className="text-center">
                <h1 className="text-lg font-bold text-white">QuantShift</h1>
                <p className="text-xs text-cyan-400">Trading Platform</p>
              </div>
            </div>
          </div>

          {/* User info */}
          <div className="px-4 py-4 border-b border-slate-800">
            <div className="flex items-center">
              <div className="flex-shrink-0 h-10 w-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
                <span className="text-white font-medium">
                  {user?.full_name?.charAt(0) || user?.email?.charAt(0) || "U"}
                </span>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-white">{user?.full_name || user?.email}</p>
                <p className="text-xs text-slate-400">{user?.role}</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
            {/* Trading Platform Section */}
            <div className="mb-6">
              <h3 className="px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                Trading Platform
              </h3>
              {platformNav.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                      isActive
                        ? "bg-cyan-600 text-white"
                        : "text-slate-300 hover:bg-slate-800 hover:text-white"
                    }`}
                  >
                    <item.icon className="h-5 w-5 mr-3" />
                    {item.name}
                  </Link>
                );
              })}
            </div>

            {/* Admin Control Center Section (admin only) */}
            {user?.role === "admin" && (
              <div>
                <h3 className="px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                  Admin Control
                </h3>
                {adminNav.map((item) => {
                  const isActive = pathname === item.href;
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                        isActive
                          ? "bg-cyan-600 text-white"
                          : "text-slate-300 hover:bg-slate-800 hover:text-white"
                      }`}
                    >
                      <item.icon className="h-5 w-5 mr-3" />
                      {item.name}
                    </Link>
                  );
                })}
              </div>
            )}
          </nav>

          {/* Logout button */}
          <div className="px-2 py-4 border-t border-slate-800">
            <button
              onClick={handleLogout}
              className="flex items-center w-full px-4 py-3 text-sm font-medium text-slate-300 rounded-lg hover:bg-slate-800 hover:text-white transition-colors"
            >
              <LogOut className="h-5 w-5 mr-3" />
              Logout
            </button>
            
            {/* Version Display */}
            <div className="mt-4 px-4 text-center">
              <p className="text-xs text-slate-500">
                {`${APP_NAME} v${APP_VERSION}`}
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
