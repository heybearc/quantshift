import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import os from 'os';

const execAsync = promisify(exec);

export const dynamic = 'force-dynamic';
export const revalidate = 0;

async function queryHAProxyConfig(): Promise<'BLUE' | 'GREEN' | null> {
  try {
    console.log('[server-info] Querying HAProxy config...');
    const { stdout, stderr } = await execAsync(
      'ssh -i /root/.ssh/id_rsa -o ConnectTimeout=2 -o StrictHostKeyChecking=no root@10.92.3.26 "grep \'use_backend quantshift.*if is_quantshift$\' /etc/haproxy/haproxy.cfg"',
      { 
        timeout: 3000,
        env: { ...process.env, HOME: '/root' }
      }
    );
    
    console.log('[server-info] HAProxy query stdout:', stdout);
    if (stderr) console.log('[server-info] HAProxy query stderr:', stderr);
    
    if (stdout.includes('quantshift-green-backend')) {
      console.log('[server-info] Detected GREEN as LIVE');
      return 'GREEN';
    } else if (stdout.includes('quantshift-blue-backend')) {
      console.log('[server-info] Detected BLUE as LIVE');
      return 'BLUE';
    }
    console.log('[server-info] Could not determine LIVE server from HAProxy config');
  } catch (error) {
    console.error('[server-info] HAProxy config query failed:', error);
  }
  return null;
}

function localIdentity(): { server: 'BLUE' | 'GREEN'; container: number; ip: string } | null {
  const addresses: string[] = [];
  for (const entries of Object.values(os.networkInterfaces())) {
    for (const entry of entries || []) {
      if (entry.family === 'IPv4') addresses.push(entry.address);
    }
  }
  const hostname = os.hostname();
  if (addresses.includes('10.92.3.30') || hostname === 'quantshift-green') {
    return { server: 'GREEN', container: 138, ip: '10.92.3.30' };
  }
  if (addresses.includes('10.92.3.29') || hostname === 'quantshift-blue') {
    return { server: 'BLUE', container: 137, ip: '10.92.3.29' };
  }
  if (process.env.SERVER_NAME === 'GREEN') {
    return { server: 'GREEN', container: 138, ip: '10.92.3.30' };
  }
  if (process.env.SERVER_NAME === 'BLUE') {
    return { server: 'BLUE', container: 137, ip: '10.92.3.29' };
  }
  return null;
}

export async function GET() {
  try {
    const identity = localIdentity();
    let server: 'BLUE' | 'GREEN' = identity?.server || 'BLUE';
    let container = identity?.container || 137;
    let ip = identity?.ip || '10.92.3.29';
    
    let status: 'LIVE' | 'STANDBY' = 'STANDBY';
    let statusSource = 'default';
    
    const haproxyLiveServer = await queryHAProxyConfig();
    if (haproxyLiveServer) {
      status = haproxyLiveServer === server ? 'LIVE' : 'STANDBY';
      statusSource = 'haproxy-config';
    } else {
      if (process.env.SERVER_STATUS) {
        status = process.env.SERVER_STATUS as 'LIVE' | 'STANDBY';
        statusSource = 'env';
      }
    }
    
    return NextResponse.json({
      server,
      status,
      ip,
      container,
      hostname: os.hostname(),
      statusSource
    });
  } catch (error) {
    console.error('Error getting server info:', error);
    return NextResponse.json({ error: 'Failed to get server info' }, { status: 500 });
  }
}
