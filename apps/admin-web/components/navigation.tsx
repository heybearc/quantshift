'use client';

import { useAuth } from '@/lib/auth-context';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
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
  LogOut,
  Menu,
  X
} from 'lucide-react';
import { useState } from 'react';
import { APP_VERSION, APP_NAME } from '@/lib/version';

export function Navigation() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Trading Platform Section
  const platformNav = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Trades', href: '/trades', icon: TrendingUp },
    { name: 'Positions', href: '/positions', icon: Activity },
    { name: 'Performance', href: '/performance', icon: BarChart3 },
    { name: 'Email Notifications', href: '/email', icon: Mail },
    { name: 'Release Notes', href: '/release-notes', icon: FileText },
  ];

  // Admin Control Center Section (admin only)
  const adminNav = [
    { name: 'User Management', href: '/users', icon: Users },
    { name: 'Session Management', href: '/admin/sessions', icon: Shield },
    { name: 'Audit Logs', href: '/admin/audit-logs', icon: FileText },
    { name: 'Health Monitor', href: '/admin/health', icon: Activity },
    { name: 'API Status', href: '/admin/api-status', icon: Zap },
    { name: 'Platform Settings', href: '/admin/settings', icon: Settings },
  ];

  const handleLogout = async () => {
    await logout();
    window.location.href = '/login';
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
        fixed inset-y-0 left-0 z-40 w-64 bg-gray-900 transform transition-transform duration-300 ease-in-out
        lg:translate-x-0 ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-center h-16 px-4 bg-gray-800">
            <h1 className="text-xl font-bold text-white">QuantShift</h1>
          </div>

          {/* User info */}
          <div className="px-4 py-4 border-b border-gray-700">
            <div className="flex items-center">
              <div className="flex-shrink-0 h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center">
                <span className="text-white font-medium">
                  {user?.full_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
                </span>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-white">{user?.full_name || user?.email}</p>
                <p className="text-xs text-gray-400">{user?.role}</p>
              </div>
            </div>
          </div>

          {/* Navigation links */}
          <nav className="flex-1 px-2 py-4 overflow-y-auto">
            {/* Trading Platform Section */}
            <div className="mb-6">
              <div className="px-4 mb-2">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Trading Platform
                </h3>
              </div>
              <div className="space-y-1">
                {platformNav.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href;
                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`
                        flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors
                        ${isActive 
                          ? 'bg-green-900/50 text-green-100 border-l-4 border-green-500' 
                          : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                        }
                      `}
                    >
                      <Icon className="h-5 w-5 mr-3" />
                      {item.name}
                    </Link>
                  );
                })}
              </div>
            </div>

            {/* Admin Control Center Section (only for admins) */}
            {user?.role === 'ADMIN' && (
              <div>
                <div className="px-4 mb-2 pt-4 border-t border-gray-700">
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    Admin Control Center
                  </h3>
                </div>
                <div className="space-y-1">
                  {adminNav.map((item) => {
                    const Icon = item.icon;
                    const isActive = pathname === item.href;
                    return (
                      <Link
                        key={item.name}
                        href={item.href}
                        onClick={() => setMobileMenuOpen(false)}
                        className={`
                          flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors
                          ${isActive 
                            ? 'bg-blue-900/50 text-blue-100 border-l-4 border-blue-500' 
                            : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                          }
                        `}
                      >
                        <Icon className="h-5 w-5 mr-3" />
                        {item.name}
                      </Link>
                    );
                  })}
                </div>
              </div>
            )}
          </nav>

          {/* Logout button */}
          <div className="px-2 py-4 border-t border-gray-700">
            <button
              onClick={handleLogout}
              className="flex items-center w-full px-4 py-3 text-sm font-medium text-gray-300 rounded-lg hover:bg-gray-800 hover:text-white transition-colors"
            >
              <LogOut className="h-5 w-5 mr-3" />
              Logout
            </button>
            
            {/* Version Display */}
            <div className="mt-4 px-4 text-center">
              <p className="text-xs text-gray-500">
                {`${APP_NAME} v${APP_VERSION}`}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-gray-600 bg-opacity-75 z-30 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}
    </>
  );
}
