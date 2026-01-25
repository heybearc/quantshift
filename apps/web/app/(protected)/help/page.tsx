"use client";

import { ProtectedRoute } from "@/components/protected-route";
import { LayoutWrapper } from "@/components/layout-wrapper";
import { useState } from "react";
import { BookOpen, Users, Shield, Activity, Mail, Settings, FileText, Search } from "lucide-react";

interface HelpSection {
  id: string;
  title: string;
  icon: any;
  content: {
    subtitle: string;
    description: string;
    steps?: string[];
  }[];
}

export default function HelpPage() {
  return (
    <ProtectedRoute>
      <LayoutWrapper>
        <HelpPageContent />
      </LayoutWrapper>
    </ProtectedRoute>
  );
}

function HelpPageContent() {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeSection, setActiveSection] = useState<string>("getting-started");

  const helpSections: HelpSection[] = [
    {
      id: "getting-started",
      title: "Getting Started",
      icon: BookOpen,
      content: [
        {
          subtitle: "Welcome to QuantShift",
          description: "QuantShift is an advanced algorithmic trading platform with comprehensive admin controls. This help documentation will guide you through all features.",
        },
        {
          subtitle: "First Steps",
          description: "After logging in, you will see the main dashboard with real-time trading data.",
          steps: [
            "Review your dashboard for current positions and performance",
            "Check the trading bot status in the sidebar",
            "Explore admin features if you have ADMIN role",
          ],
        },
      ],
    },
    {
      id: "user-management",
      title: "User Management",
      icon: Users,
      content: [
        {
          subtitle: "Managing Users",
          description: "Admin users can create, edit, and manage all platform users.",
          steps: [
            "Navigate to User Management from the Admin Control Center",
            "Click Add User to create new accounts",
            "Set appropriate roles: SUPER_ADMIN, ADMIN, TRADER, VIEWER, or API_USER",
            "Configure enterprise fields like phone, timezone, and trading permissions",
            "Approve or deactivate user accounts as needed",
          ],
        },
        {
          subtitle: "User Roles",
          description: "Different roles have different permissions:",
          steps: [
            "SUPER_ADMIN: Full system access including user management",
            "ADMIN: Administrative access to most features",
            "TRADER: Can execute trades and view positions",
            "VIEWER: Read-only access to trading data",
            "API_USER: Programmatic API access only",
          ],
        },
      ],
    },
    {
      id: "sessions-audit",
      title: "Sessions & Audit Logs",
      icon: Shield,
      content: [
        {
          subtitle: "Session Management",
          description: "Monitor and control active user sessions.",
          steps: [
            "View all active sessions with user details",
            "See last activity time, browser, and IP address",
            "Terminate suspicious sessions immediately",
            "Review session statistics (active/inactive/total)",
          ],
        },
        {
          subtitle: "Audit Logs",
          description: "Track all system actions for security and compliance.",
          steps: [
            "Filter logs by action type (CREATE, UPDATE, DELETE, LOGIN)",
            "Search by user email, action, or resource",
            "Review changes made to system settings",
            "Export audit logs for compliance reporting",
          ],
        },
      ],
    },
    {
      id: "monitoring",
      title: "System Monitoring",
      icon: Activity,
      content: [
        {
          subtitle: "Health Monitor",
          description: "Real-time system health and performance metrics.",
          steps: [
            "Monitor memory usage and CPU load",
            "Check database health and response times",
            "View system uptime and platform information",
            "Enable auto-refresh for continuous monitoring",
          ],
        },
        {
          subtitle: "API Status",
          description: "Monitor critical API endpoint health.",
          steps: [
            "View operational status of all endpoints",
            "Check response times for performance issues",
            "Identify degraded or down endpoints",
            "Use auto-refresh to track real-time status",
          ],
        },
      ],
    },
    {
      id: "email-settings",
      title: "Email Configuration",
      icon: Mail,
      content: [
        {
          subtitle: "Gmail Setup",
          description: "Configure Gmail for platform notifications.",
          steps: [
            "Go to Platform Settings → Email Configuration",
            "Select Gmail (Recommended)",
            "Enter your Gmail email address",
            "Generate an App Password from Google Account Security",
            "IMPORTANT: Remove ALL spaces from the App Password",
            "Enter the App Password (16 characters, no spaces)",
            "Configure From Name and From Email",
            "Click Send Test Email to verify",
          ],
        },
        {
          subtitle: "SMTP Setup",
          description: "Configure custom SMTP server for emails.",
          steps: [
            "Select Custom SMTP",
            "Enter SMTP server address and port",
            "Provide SMTP username and password",
            "Enable secure connection (TLS/SSL)",
            "Configure email sender information",
            "Test the configuration",
          ],
        },
      ],
    },
    {
      id: "general-settings",
      title: "General Settings",
      icon: Settings,
      content: [
        {
          subtitle: "Platform Configuration",
          description: "Customize platform name, description, and behavior.",
          steps: [
            "Navigate to Platform Settings → General Settings",
            "Update platform name and description",
            "Configure maintenance mode if needed",
            "Set user registration policies",
            "Adjust security settings (session timeout, login attempts)",
          ],
        },
      ],
    },
    {
      id: "release-notes",
      title: "Release Notes",
      icon: FileText,
      content: [
        {
          subtitle: "Viewing Release Notes",
          description: "Stay updated with platform changes and improvements.",
          steps: [
            "Navigate to Release Notes from the navigation menu",
            "View detailed changelogs for each version",
            "See features, improvements, and bug fixes",
            "Dismiss release banners after reviewing",
          ],
        },
      ],
    },
  ];

  const filteredSections = searchQuery
    ? helpSections.filter(
        (section) =>
          section.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          section.content.some(
            (c) =>
              c.subtitle.toLowerCase().includes(searchQuery.toLowerCase()) ||
              c.description.toLowerCase().includes(searchQuery.toLowerCase())
          )
      )
    : helpSections;

  const displaySection = searchQuery
    ? filteredSections
    : helpSections.filter((s) => s.id === activeSection);

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Help & Documentation</h1>
          <p className="text-slate-400">Comprehensive guides for all QuantShift features</p>
        </div>

        <div className="relative">
          <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400" />
          <input
            type="text"
            placeholder="Search documentation..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-12 pr-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-1">
            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-4 sticky top-8">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Sections</h3>
              <nav className="space-y-1">
                {helpSections.map((section) => (
                  <button
                    key={section.id}
                    onClick={() => {
                      setActiveSection(section.id);
                      setSearchQuery("");
                    }}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                      activeSection === section.id && !searchQuery
                        ? "bg-cyan-600 text-white"
                        : "text-slate-300 hover:bg-slate-700"
                    }`}
                  >
                    <section.icon className="h-4 w-4" />
                    <span>{section.title}</span>
                  </button>
                ))}
              </nav>
            </div>
          </div>

          <div className="lg:col-span-3 space-y-6">
            {displaySection.length === 0 ? (
              <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-8 text-center">
                <p className="text-slate-400">No results found for "{searchQuery}"</p>
              </div>
            ) : (
              displaySection.map((section) => (
                <div
                  key={section.id}
                  id={section.id}
                  className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6"
                >
                  <div className="flex items-center gap-3 mb-6">
                    <div className="h-10 w-10 bg-cyan-600/20 rounded-lg flex items-center justify-center">
                      <section.icon className="h-5 w-5 text-cyan-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-white">{section.title}</h2>
                  </div>

                  <div className="space-y-6">
                    {section.content.map((item, idx) => (
                      <div key={idx}>
                        <h3 className="text-lg font-semibold text-white mb-2">{item.subtitle}</h3>
                        <p className="text-slate-300 mb-3">{item.description}</p>
                        {item.steps && (
                          <ul className="space-y-2">
                            {item.steps.map((step, stepIdx) => (
                              <li key={stepIdx} className="flex items-start gap-3 text-slate-400">
                                <span className="text-cyan-400 mt-1">•</span>
                                <span>{step}</span>
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
