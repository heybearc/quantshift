module.exports = {
  apps: [{
    name: 'quantshift-admin',
    script: 'npm',
    args: 'start',
    cwd: '/opt/quantshift/apps/admin-web',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      PORT: 3001
    },
    error_file: '/var/log/quantshift/admin-error.log',
    out_file: '/var/log/quantshift/admin-out.log',
    log_file: '/var/log/quantshift/admin-combined.log',
    time: true
  }]
};
