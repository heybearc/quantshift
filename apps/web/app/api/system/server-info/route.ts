import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import os from 'os';

const execAsync = promisify(exec);

async function queryHAProxyConfig(): Promise<'BLUE' | 'GREEN' | null> {
  try {
    const { stdout } = await execAsync(
      'ssh -o ConnectTimeout=2 -o StrictHostKeyChecking=no root@10.92.3.26 "grep \'use_backend quantshift.*if is_quantshift$\' /etc/haproxy/haproxy.cfg"',
      { timeout: 3000 }
    );
    
    if (stdout.includes('quantshift_green')) {
      return 'GREEN';
    } else if (stdout.includes('quantshift_blue')) {
      return 'BLUE';
    }
  } catch (error) {
    console.error('HAProxy config query failed:', error);
  }
  return null;
}

export async function GET() {
  try {
    let server: 'BLUE' | 'GREEN' = 'BLUE';
    let container = 137;
    let ip = '10.92.3.29';
    
    try {
      const { stdout } = await execAsync('hostname -I 2>/dev/null || hostname -i 2>/dev/null');
      const localIp = stdout.trim().split(' ')[0];
      
      if (localIp.includes('10.92.3.30')) {
        server = 'GREEN';
        container = 138;
        ip = '10.92.3.30';
      } else if (localIp.includes('10.92.3.29')) {
        server = 'BLUE';
        container = 137;
        ip = '10.92.3.29';
      }
    } catch (error) {
      if (process.env.SERVER_NAME === 'GREEN') {
        server = 'GREEN';
        container = 138;
        ip = '10.92.3.29';
      }
    }
    
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
