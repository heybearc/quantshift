"use client";

import { useAuth } from "@/lib/auth-context";
import { Navigation } from "@/components/navigation";
import { ReleaseBanner } from "@/components/release-banner";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { Mail, Send, Save, AlertCircle, CheckCircle, Eye, EyeOff, Loader2 } from "lucide-react";

interface EmailSettings {
  authType: "gmail" | "smtp";
  gmailEmail: string;
  gmailAppPassword: string;
  smtpServer: string;
  smtpPort: string;
  smtpUser: string;
  smtpPassword: string;
  smtpSecure: boolean;
  fromEmail: string;
  fromName: string;
  replyToEmail: string;
}

export default function EmailSettingsPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [settings, setSettings] = useState<EmailSettings>({
    authType: "gmail",
    gmailEmail: "",
    gmailAppPassword: "",
    smtpServer: "smtp.gmail.com",
    smtpPort: "587",
    smtpUser: "",
    smtpPassword: "",
    smtpSecure: true,
    fromEmail: "",
    fromName: "QuantShift Trading Platform",
    replyToEmail: "",
  });
  const [testEmail, setTestEmail] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
    if (!authLoading && user && user.role?.toUpperCase() !== "ADMIN") {
      router.push("/dashboard");
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user?.role?.toUpperCase() === "ADMIN") {
      fetchSettings();
      setTestEmail(user.email || "");
    }
  }, [user]);

  const fetchSettings = async () => {
    try {
      const response = await fetch("/api/admin/settings/email", {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.data) {
          setSettings(data.data);
        }
      }
    } catch (error) {
      console.error("Error fetching email settings:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setMessage(null);
    setSaving(true);

    try {
      const response = await fetch("/api/admin/settings/email", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(settings),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setMessage({ type: "success", text: "Email settings saved successfully" });
      } else {
        setMessage({ type: "error", text: data.error || "Failed to save settings" });
      }
    } catch (error) {
      setMessage({ type: "error", text: "Failed to save settings" });
    } finally {
      setSaving(false);
    }
  };

  const handleTestEmail = async () => {
    if (!testEmail) {
      setMessage({ type: "error", text: "Please enter a test email address" });
      return;
    }

    setMessage(null);
    setTesting(true);

    try {
      const response = await fetch("/api/admin/settings/email/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email: testEmail }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setMessage({ type: "success", text: `Test email sent to ${testEmail}` });
      } else {
        setMessage({ type: "error", text: data.error || "Failed to send test email" });
      }
    } catch (error) {
      setMessage({ type: "error", text: "Failed to send test email" });
    } finally {
      setTesting(false);
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500"></div>
      </div>
    );
  }

  if (!user || user.role?.toUpperCase() !== "ADMIN") {
    return null;
  }

  const isGmailConfigValid = settings.authType === "gmail" && settings.gmailEmail && settings.gmailAppPassword;
  const isSmtpConfigValid = settings.authType === "smtp" && settings.smtpServer && settings.smtpUser && settings.smtpPassword;
  const isConfigValid = (isGmailConfigValid || isSmtpConfigValid) && settings.fromEmail && settings.fromName;

  return (
    <div className="flex h-screen bg-slate-900">
      <Navigation />
      <main className="flex-1 lg:ml-64 overflow-y-auto">
        {user && <ReleaseBanner userId={user.id} />}
        <div className="p-8">
          <div className="space-y-6">
            <div>
              <h1 className="text-3xl font-bold text-white">Email Configuration</h1>
              <p className="text-slate-400 mt-2">Configure SMTP or Gmail settings for email notifications</p>
            </div>

            {message && (
              <div
                className={`p-4 rounded-xl border flex items-center gap-3 ${
                  message.type === "success"
                    ? "bg-green-900/20 border-green-700 text-green-400"
                    : "bg-red-900/20 border-red-700 text-red-400"
                }`}
              >
                {message.type === "success" ? (
                  <CheckCircle className="h-5 w-5" />
                ) : (
                  <AlertCircle className="h-5 w-5" />
                )}
                <p className="text-sm">{message.text}</p>
              </div>
            )}

            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
              <h2 className="text-xl font-semibold text-white mb-6">Authentication Method</h2>
              
              <div className="flex gap-4 mb-6">
                <button
                  onClick={() => setSettings({ ...settings, authType: "gmail" })}
                  className={`flex-1 px-4 py-3 rounded-lg font-medium transition-colors ${
                    settings.authType === "gmail"
                      ? "bg-cyan-600 text-white"
                      : "bg-slate-700 text-slate-300 hover:bg-slate-600"
                  }`}
                >
                  Gmail App Password
                </button>
                <button
                  onClick={() => setSettings({ ...settings, authType: "smtp" })}
                  className={`flex-1 px-4 py-3 rounded-lg font-medium transition-colors ${
                    settings.authType === "smtp"
                      ? "bg-cyan-600 text-white"
                      : "bg-slate-700 text-slate-300 hover:bg-slate-600"
                  }`}
                >
                  SMTP Server
                </button>
              </div>

              {settings.authType === "gmail" ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Gmail Address</label>
                    <input
                      type="email"
                      value={settings.gmailEmail}
                      onChange={(e) => setSettings({ ...settings, gmailEmail: e.target.value })}
                      className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                      placeholder="your-email@gmail.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">App Password</label>
                    <div className="relative">
                      <input
                        type={showPassword ? "text" : "password"}
                        value={settings.gmailAppPassword}
                        onChange={(e) => setSettings({ ...settings, gmailAppPassword: e.target.value })}
                        className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        placeholder="xxxx xxxx xxxx xxxx"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-white"
                      >
                        {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                      </button>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      Generate an app password in your Google Account settings
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">SMTP Server</label>
                      <input
                        type="text"
                        value={settings.smtpServer}
                        onChange={(e) => setSettings({ ...settings, smtpServer: e.target.value })}
                        className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        placeholder="smtp.example.com"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">Port</label>
                      <input
                        type="text"
                        value={settings.smtpPort}
                        onChange={(e) => setSettings({ ...settings, smtpPort: e.target.value })}
                        className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        placeholder="587"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Username</label>
                    <input
                      type="text"
                      value={settings.smtpUser}
                      onChange={(e) => setSettings({ ...settings, smtpUser: e.target.value })}
                      className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                      placeholder="username"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-2">Password</label>
                    <div className="relative">
                      <input
                        type={showPassword ? "text" : "password"}
                        value={settings.smtpPassword}
                        onChange={(e) => setSettings({ ...settings, smtpPassword: e.target.value })}
                        className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        placeholder="••••••••"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-white"
                      >
                        {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                      </button>
                    </div>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="smtpSecure"
                      checked={settings.smtpSecure}
                      onChange={(e) => setSettings({ ...settings, smtpSecure: e.target.checked })}
                      className="w-4 h-4 text-cyan-600 bg-slate-900 border-slate-700 rounded focus:ring-cyan-500"
                    />
                    <label htmlFor="smtpSecure" className="ml-2 text-sm text-slate-300">
                      Use TLS/SSL
                    </label>
                  </div>
                </div>
              )}
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
              <h2 className="text-xl font-semibold text-white mb-6">Email Details</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">From Email</label>
                  <input
                    type="email"
                    value={settings.fromEmail}
                    onChange={(e) => setSettings({ ...settings, fromEmail: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    placeholder="noreply@quantshift.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">From Name</label>
                  <input
                    type="text"
                    value={settings.fromName}
                    onChange={(e) => setSettings({ ...settings, fromName: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    placeholder="QuantShift Trading Platform"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Reply-To Email (Optional)</label>
                  <input
                    type="email"
                    value={settings.replyToEmail}
                    onChange={(e) => setSettings({ ...settings, replyToEmail: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    placeholder="support@quantshift.com"
                  />
                </div>
              </div>
            </div>

            <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6">
              <h2 className="text-xl font-semibold text-white mb-6">Test Email</h2>
              
              <div className="flex gap-4">
                <input
                  type="email"
                  value={testEmail}
                  onChange={(e) => setTestEmail(e.target.value)}
                  className="flex-1 px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  placeholder="test@example.com"
                />
                <button
                  onClick={handleTestEmail}
                  disabled={testing || !isConfigValid}
                  className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {testing ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4" />
                      Send Test
                    </>
                  )}
                </button>
              </div>
              {!isConfigValid && (
                <p className="text-xs text-yellow-400 mt-2">
                  Please configure all required fields before testing
                </p>
              )}
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-2 px-6 py-3 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4" />
                    Save Settings
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
