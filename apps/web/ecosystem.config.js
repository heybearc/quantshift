module.exports = {
  apps: [{
    name: "quantshift-admin",
    script: "npm",
    args: "start",
    cwd: "/opt/quantshift/apps/web",
    env: {
      NODE_ENV: "production",
      DATABASE_URL: "postgresql://quantshift:Cloudy_92!@10.92.3.21:5432/quantshift",
      JWT_SECRET: "quantshift-production-secret-key-2024-change-this-in-production",
      NEXTAUTH_URL: "http://10.92.3.29:3001"
    },
    instances: 1,
    exec_mode: "fork",
    autorestart: true,
    watch: false,
    max_memory_restart: "1G"
  }]
};
