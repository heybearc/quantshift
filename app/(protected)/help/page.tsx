"use client";

import { useEffect } from "react";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { BookOpen, ExternalLink, FileText, Video, MessageCircle, Mail } from "lucide-react";

export default function HelpPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const helpSections = [
    {
      title: "Getting Started",
      icon: BookOpen,
      items: [
        { name: "Platform Overview", description: "Learn about QuantShift features and capabilities", link: "/dashboard" },
        { name: "Trading Strategies", description: "Understanding the MA Crossover strategy", link: "/performance" },
        { name: "Risk Management", description: "How position sizing and stops work", link: "/settings" },
      ],
    },
    {
      title: "Documentation",
      icon: FileText,
      items: [
        { name: "API Reference", description: "Complete API documentation", link: "/admin/api-status" },
        { name: "Configuration Guide", description: "Customize bot settings and parameters", link: "/settings" },
        { name: "Performance Metrics", description: "Understanding your trading statistics", link: "/performance" },
      ],
    },
    {
      title: "Platform Pages",
      icon: Video,
      items: [
        { name: "Dashboard", description: "Navigate the trading dashboard", link: "/dashboard" },
        { name: "Trades History", description: "View your trading history", link: "/trades" },
        { name: "Open Positions", description: "Monitor and manage open trades", link: "/positions" },
      ],
    },
  ];

  return (
    <div className="flex h-screen bg-slate-900">
      <Navigation />
      <main className="flex-1 lg:ml-64 overflow-y-auto">
        {user && <ReleaseBanner userId={user.id} />}
        <div className="p-8">
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold text-white">Help & Documentation</h1>
              <p className="text-slate-400 mt-2">Resources to help you get the most out of QuantShift</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {helpSections.map((section) => (
                <div key={section.title} className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <section.icon className="h-6 w-6 text-cyan-500" />
                    <h2 className="text-xl font-semibold text-white">{section.title}</h2>
                  </div>
                  <div className="space-y-3">
                    {section.items.map((item) => (
                      <Link key={item.name} href={item.link} className="group cursor-pointer block">
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="text-sm font-medium text-white group-hover:text-cyan-400 transition-colors">
                              {item.name}
                            </h3>
                            <p className="text-xs text-slate-400 mt-1">{item.description}</p>
                          </div>
                          <ExternalLink className="h-4 w-4 text-slate-500 group-hover:text-cyan-400 transition-colors" />
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
              <div className="flex items-start gap-4">
                <MessageCircle className="h-6 w-6 text-cyan-500 mt-1" />
                <div>
                  <h2 className="text-xl font-semibold text-white mb-2">Need More Help?</h2>
                  <p className="text-slate-400 mb-4">
                    Cant find what youre looking for? Our support team is here to help.
                  </p>
                  <a 
                    href="mailto:support@quantshift.com" 
                    className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg transition-colors"
                  >
                    <Mail className="h-4 w-4" />
                    Contact Support
                  </a>
                </div>
              </div>
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
              <h2 className="text-xl font-semibold text-white mb-4">Quick Links</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Link href="/release-notes" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300 transition-colors">
                  <ExternalLink className="h-4 w-4" />
                  <span>Release Notes</span>
                </Link>
                <Link href="/dashboard" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300 transition-colors">
                  <ExternalLink className="h-4 w-4" />
                  <span>Trading Dashboard</span>
                </Link>
                <Link href="/settings" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300 transition-colors">
                  <ExternalLink className="h-4 w-4" />
                  <span>Platform Settings</span>
                </Link>
                {user?.role?.toUpperCase() === "ADMIN" && (
                  <Link href="/users" className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300 transition-colors">
                    <ExternalLink className="h-4 w-4" />
                    <span>User Management</span>
                  </Link>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
