module.exports = {
  apps: [{
    name: "quantshift-admin",
    script: "npm",
    args: "start",
    cwd: "/opt/quantshift/apps/web",
    env: {
      NODE_ENV: "production",
      DATABASE_URL: process.env.DATABASE_URL,
      JWT_SECRET: process.env.JWT_SECRET,
      NEXTAUTH_URL: "http://10.92.3.29:3001"
    },
    instances: 1,
    exec_mode: "fork",
    autorestart: true,
    watch: false,
    max_memory_restart: "1G"
  }]
};
