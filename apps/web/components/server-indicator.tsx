'use client';

import { useState, useEffect } from 'react';

interface ServerInfo {
  server: 'BLUE' | 'GREEN';
  status: 'LIVE' | 'STANDBY';
  ip: string;
  container: number;
}

export function ServerIndicator() {
  const [serverInfo, setServerInfo] = useState<ServerInfo | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    fetchServerInfo();
    const interval = setInterval(fetchServerInfo, 300000);
    return () => clearInterval(interval);
  }, []);

  const fetchServerInfo = async () => {
    try {
      const response = await fetch('/api/system/server-info');
      if (response.ok) {
        const data = await response.json();
        setServerInfo(data);
      }
    } catch (error) {
      // Silently fail - indicator just won't show
    }
  };

  if (!serverInfo) return null;

  // Show container color (Blue container = blue dot, Green container = green dot)
  const containerColor = serverInfo.server === 'BLUE' ? 'bg-blue-500' : 'bg-green-500';
  // Status emoji shows LIVE (bright) vs STANDBY (dimmer)
  const statusEmoji = serverInfo.status === 'LIVE' ? '⚡' : '○';

  return (
    <div 
      className="relative inline-block"
      onMouseEnter={() => setShowDetails(true)}
      onMouseLeave={() => setShowDetails(false)}
    >
      <div className="flex items-center space-x-1 cursor-help">
        <div className={`w-2 h-2 rounded-full ${containerColor} ${serverInfo.status === 'LIVE' ? 'opacity-100' : 'opacity-50'}`} />
      </div>

      {showDetails && (
        <div className="absolute bottom-full right-0 mb-2 px-3 py-2 bg-slate-800 text-white text-xs rounded shadow-lg whitespace-nowrap z-50 border border-slate-700">
          <div className="space-y-1">
            <div className="font-semibold">{statusEmoji} {serverInfo.server} - {serverInfo.status}</div>
            <div className="text-slate-300">Container {serverInfo.container}</div>
            <div className="text-slate-400 text-[10px]">{serverInfo.ip}</div>
          </div>
          <div className="absolute top-full right-4 -mt-1">
            <div className="border-4 border-transparent border-t-slate-800" />
          </div>
        </div>
      )}
    </div>
  );
}
