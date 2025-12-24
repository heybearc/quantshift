module.exports = {
  apps: [{
    name: 'quantshift-dashboard',
    script: 'npm',
    args: 'start',
    cwd: '/opt/quantshift/apps/dashboard',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      NODE_ENV: 'production',
      PORT: 3000,
      DATABASE_URL: 'postgresql://quantshift_dashboard:Cloudy_92!@10.92.3.21:5432/quantshift'
    }
  }]
}
