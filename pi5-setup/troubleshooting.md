# Bitcoin Ben's Burger Bus Club - Pi5 Troubleshooting Guide

## Common Issues and Solutions

### 1. Installation Issues

#### MongoDB Installation Failed
```bash
# Check if MongoDB service started
sudo systemctl status mongod

# If not, try manual start
sudo systemctl start mongod

# Check logs for errors
sudo journalctl -u mongod -f

# For arm64 compatibility issues:
sudo apt install mongodb-server-core mongodb-clients
```

#### Node.js Memory Issues
```bash
# Increase Node.js memory limit
export NODE_OPTIONS="--max-old-space-size=2048"

# Add to ~/.bashrc for permanent fix
echo 'export NODE_OPTIONS="--max-old-space-size=2048"' >> ~/.bashrc
```

#### Python Dependencies Failed
```bash
# Update pip and try again
source ~/bitcoin-bens-club/venv/bin/activate
pip install --upgrade pip setuptools wheel

# Install build dependencies
sudo apt install python3-dev libffi-dev libssl-dev

# Retry installation
pip install -r requirements.txt
```

### 2. Service Issues

#### Backend Won't Start
```bash
# Check service status
sudo systemctl status bbc-backend

# View detailed logs
sudo journalctl -u bbc-backend -f

# Manual start for debugging
cd ~/bitcoin-bens-club/backend
source ../venv/bin/activate
python server.py

# Common fixes:
# 1. Check .env file exists
# 2. Verify MongoDB is running
# 3. Check port 8001 isn't in use
sudo netstat -tlnp | grep 8001
```

#### Frontend Won't Start
```bash
# Check PM2 status
pm2 status

# View PM2 logs
pm2 logs bbc-frontend

# Manual start for debugging
cd ~/bitcoin-bens-club/frontend
yarn start

# Common fixes:
# 1. Clear node_modules and reinstall
rm -rf node_modules package-lock.json yarn.lock
yarn install

# 2. Check port 3000 isn't in use
sudo netstat -tlnp | grep 3000
```

#### MongoDB Connection Issues
```bash
# Test MongoDB connection
mongosh --eval "db.adminCommand('ismaster')"

# Check if authentication is working
mongosh -u bbcadmin -p --authenticationDatabase admin

# Reset MongoDB if needed
sudo systemctl stop mongod
sudo rm -rf /var/lib/mongodb/*
sudo systemctl start mongod
# Re-run setup script
```

### 3. Network Access Issues

#### Can't Access from Other Devices
```bash
# Check if services are binding to all interfaces
sudo netstat -tlnp | grep ":3000\|:8001"
# Should show 0.0.0.0:3000 and 0.0.0.0:8001

# Check firewall
sudo ufw status
# Should allow ports 3000 and 8001

# Test local access first
curl http://localhost:3000
curl http://localhost:8001/api/

# Get Pi5 IP address
hostname -I

# Test from another device on same network
curl http://PI5_IP:3000
```

#### Internet Access Not Working
```bash
# Check router port forwarding
# External Port -> Internal IP:Port
# 80 -> 192.168.1.XXX:3000
# 8001 -> 192.168.1.XXX:8001

# Check external IP
curl ifconfig.me

# Test port accessibility
# Use online port checker tools

# Check ISP restrictions
# Some ISPs block incoming connections on residential plans
```

### 4. Performance Issues

#### High Memory Usage
```bash
# Check memory usage
free -h
htop

# Optimize MongoDB
echo "storage.wiredTiger.engineConfig.cacheSizeGB: 0.5" | sudo tee -a /etc/mongod.conf
sudo systemctl restart mongod

# Optimize Node.js
export NODE_OPTIONS="--max-old-space-size=1024"

# Consider using production build for frontend
cd ~/bitcoin-bens-club/frontend
yarn build
# Serve build folder instead of dev server
```

#### Slow Performance
```bash
# Check SD card speed
sudo hdparm -t /dev/mmcblk0

# Consider using SSD via USB 3.0
# Move data directory to faster storage

# Enable swap if needed (not recommended for SD cards)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # Set CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### 5. Database Issues

#### Database Connection Lost
```bash
# Check MongoDB status
sudo systemctl status mongod

# Restart MongoDB
sudo systemctl restart mongod

# Check for corruption
mongosh --eval "db.runCommand({dbStats: 1})"

# Repair if needed
mongod --repair --dbpath /var/lib/mongodb
```

#### Data Loss Prevention
```bash
# Setup automatic backups
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd ~/bitcoin-bens-club && ./scripts/backup.sh

# Test backup/restore process
./scripts/backup.sh
# Verify backup file created in ~/bitcoin-bens-club/backups/
```

### 6. SSL/HTTPS Issues

#### Let's Encrypt Certificate Failed
```bash
# Check domain DNS resolution
nslookup your-domain.com

# Ensure port 80 is accessible from internet
sudo ufw allow 80/tcp

# Try manual certificate generation
sudo certbot certonly --standalone -d your-domain.com

# Check certificate status
sudo certbot certificates
```

### 7. Admin Panel Access Issues

#### Admin Login Not Working
```bash
# Check admin credentials in .env file
cat ~/bitcoin-bens-club/backend/.env | grep ADMIN

# Test admin login endpoint
curl -X POST http://localhost:8001/api/auth/admin-login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@bitcoinben.local","password":"your-password"}'

# Check backend logs for authentication errors
sudo journalctl -u bbc-backend -f
```

### 8. Update Issues

#### Update Script Failed
```bash
# Manual update process
cd ~/bitcoin-bens-club

# Stop services
./scripts/stop.sh

# Update system
sudo apt update && sudo apt upgrade -y

# Update Node.js packages
cd frontend
yarn install
yarn build

# Update Python packages
cd ../backend
source ../venv/bin/activate
pip install --upgrade -r requirements.txt

# Start services
cd ..
./scripts/start.sh
```

## Diagnostic Scripts

### System Health Check
```bash
#!/bin/bash
echo "🔍 Bitcoin Ben's System Health Check"
echo "==================================="

echo "📊 System Resources:"
echo "CPU Temperature: $(vcgencmd measure_temp)"
echo "Memory: $(free -h | grep Mem)"
echo "Disk: $(df -h / | tail -1)"
echo "Load: $(uptime | cut -d',' -f3-)"

echo -e "\n🔧 Services Status:"
sudo systemctl is-active mongod
sudo systemctl is-active bbc-backend
pm2 show bbc-frontend 2>/dev/null | grep status || echo "Frontend: Not running"

echo -e "\n🌐 Network:"
echo "Local IP: $(hostname -I | awk '{print $1}')"
echo "External IP: $(curl -s ifconfig.me)"

echo -e "\n🗄️ Database:"
mongosh --quiet --eval "db.adminCommand('ping')" 2>/dev/null && echo "MongoDB: Connected" || echo "MongoDB: Disconnected"
```

### Log Aggregator
```bash
#!/bin/bash
echo "📋 Recent Logs Summary"
echo "====================="

echo "🔧 Backend Logs (last 10 lines):"
sudo journalctl -u bbc-backend -n 10 --no-pager

echo -e "\n⚛️ Frontend Logs:"
pm2 logs bbc-frontend --lines 10 2>/dev/null || echo "No PM2 logs available"

echo -e "\n🗄️ MongoDB Logs (last 5 lines):"
sudo tail -5 /var/log/mongodb/mongod.log 2>/dev/null || echo "No MongoDB logs found"

echo -e "\n🔒 Security Logs (failed logins):"
sudo grep "Failed password" /var/log/auth.log | tail -5
```

### Port Check Script
```bash
#!/bin/bash
echo "🔍 Port Accessibility Check"
echo "=========================="

check_port() {
    local port=$1
    local service=$2
    
    if nc -z localhost $port 2>/dev/null; then
        echo "✅ $service (port $port): Accessible locally"
    else
        echo "❌ $service (port $port): Not accessible"
    fi
}

check_port 3000 "Frontend"
check_port 8001 "Backend API"
check_port 27017 "MongoDB"

echo -e "\n🌐 External Access Test:"
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo "Test these URLs from another device:"
echo "Frontend: http://$LOCAL_IP:3000"
echo "Backend: http://$LOCAL_IP:8001/api/"
echo "Admin: http://$LOCAL_IP:3000?admin=true"
```

## Getting Help

### Log Collection for Support
```bash
# Create comprehensive log package
mkdir -p ~/bbc-debug-$(date +%Y%m%d)
cd ~/bbc-debug-$(date +%Y%m%d)

# System info
uname -a > system-info.txt
free -h > memory-info.txt
df -h > disk-info.txt

# Service logs
sudo journalctl -u bbc-backend -n 50 > backend-logs.txt
pm2 logs bbc-frontend --lines 50 > frontend-logs.txt 2>/dev/null
sudo journalctl -u mongod -n 20 > mongodb-logs.txt

# Configuration (remove sensitive data)
cp ~/bitcoin-bens-club/backend/.env backend-env.txt
sed -i 's/PASSWORD=.*/PASSWORD=***REDACTED***/g' backend-env.txt
sed -i 's/SECRET=.*/SECRET=***REDACTED***/g' backend-env.txt

# Network info
ip addr > network-config.txt
sudo netstat -tlnp > listening-ports.txt

# Package everything
cd ..
tar -czf bbc-debug-$(date +%Y%m%d).tar.gz bbc-debug-$(date +%Y%m%d)/

echo "Debug package created: bbc-debug-$(date +%Y%m%d).tar.gz"
```

### Recovery Mode
If everything fails, use this recovery procedure:

1. **Backup current data:**
   ```bash
   ./scripts/backup.sh
   ```

2. **Stop all services:**
   ```bash
   ./scripts/stop.sh
   sudo systemctl stop mongod
   ```

3. **Reset to clean state:**
   ```bash
   cd ~
   mv bitcoin-bens-club bitcoin-bens-club-backup
   ```

4. **Re-run setup:**
   ```bash
   ./setup-pi5.sh
   ```

5. **Restore data:**
   ```bash
   # Restore from backup created in step 1
   ```

Remember: Always backup before making major changes!