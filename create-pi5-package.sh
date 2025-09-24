#!/bin/bash

# Create complete Bitcoin Ben's Pi5 package
echo "📦 Creating Complete Bitcoin Ben's Pi5 Package..."

PACKAGE_NAME="bitcoin-bens-pi5-complete"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_DIR="${PACKAGE_NAME}_${TIMESTAMP}"

# Create package structure
mkdir -p "$PACKAGE_DIR"/{setup,app-source,docs,scripts,tools}

echo "📁 Copying setup scripts..."
# Copy setup scripts
cp pi5-setup/*.sh "$PACKAGE_DIR/setup/" 2>/dev/null || true
cp pi5-setup/*.md "$PACKAGE_DIR/docs/" 2>/dev/null || true
cp pi5-complete-package/*.sh "$PACKAGE_DIR/setup/" 2>/dev/null || true

echo "📁 Copying application source..."
# Copy application source
cp -r backend "$PACKAGE_DIR/app-source/" 2>/dev/null && {
    # Clean backend
    rm -f "$PACKAGE_DIR/app-source/backend/.env"
    rm -rf "$PACKAGE_DIR/app-source/backend/__pycache__"
    rm -rf "$PACKAGE_DIR/app-source/backend/venv"
    
    # Create env template
    cat > "$PACKAGE_DIR/app-source/backend/.env.template" << 'EOF'
# Database Configuration (auto-generated)
MONGO_URL="mongodb://localhost:27017/bitcoin_bens_club"
DB_NAME="bitcoin_bens_club"

# Server Configuration  
HOST=0.0.0.0
PORT=8001

# Security (auto-generated)
JWT_SECRET_KEY=""
ADMIN_EMAIL="admin@bitcoinben.local"
ADMIN_PASSWORD=""

# BCH Configuration
BCH_RECEIVING_ADDRESS="bitcoincash:qph0duvh0zn0r2um7znh8gx20p50dr3ycc5lcp0sc4"

# Pump.fun Token
PUMP_FUN_TOKEN_ADDRESS="mWusXdRfsYAoFtYdaDcf8tmG7hnRNvnVc2TuvNEpump"
EOF
}

cp -r frontend "$PACKAGE_DIR/app-source/" 2>/dev/null && {
    # Clean frontend
    rm -rf "$PACKAGE_DIR/app-source/frontend/node_modules"
    rm -rf "$PACKAGE_DIR/app-source/frontend/build"
    rm -f "$PACKAGE_DIR/app-source/frontend/.env"
    rm -f "$PACKAGE_DIR/app-source/frontend/yarn.lock"
    rm -f "$PACKAGE_DIR/app-source/frontend/package-lock.json"
    
    # Create env template
    cat > "$PACKAGE_DIR/app-source/frontend/.env.template" << 'EOF'
# Backend Configuration (auto-configured)
REACT_APP_BACKEND_URL=http://localhost:8001
GENERATE_SOURCEMAP=false
EOF
}

echo "📚 Creating documentation..."
# Main README
cat > "$PACKAGE_DIR/README.md" << 'EOF'
# 🍔 Bitcoin Ben's Burger Bus Club - Complete Pi5 Package

## 🚀 ONE-COMMAND INSTALLATION

Run this on your Raspberry Pi 5:

```bash
wget https://bitcoin-bens.com/pi5-package.tar.gz
tar -xzf pi5-package.tar.gz
cd bitcoin-bens-pi5-complete_*/
chmod +x setup/install.sh
./setup/install.sh
```

## ✨ What You Get

### 🏗️ Complete Application Stack
- Bitcoin Ben's Burger Bus Club (Full-Stack App)
- MongoDB 7.0 with authentication
- Node.js 18.x LTS + Python 3.11+
- PM2 Process Manager + Nginx
- Systemd services for auto-start

### 🌐 Internet & Security  
- SSL certificates (Let's Encrypt)
- VPN access (Tailscale/WireGuard)
- Enhanced firewall (UFW + Fail2Ban)
- Dynamic DNS (DuckDNS/No-IP)
- Automatic port forwarding (UPnP)

### 📊 Monitoring & Management
- Real-time system monitoring
- Automated daily backups
- Health checks & email alerts
- Easy management scripts
- Comprehensive logging

## 🎯 Quick Access After Setup

- **Frontend:** `http://your-pi-ip:3000`
- **Admin Panel:** `http://your-pi-ip:3000?admin=true`
- **API Docs:** `http://your-pi-ip:8001/docs`

## 🛠️ Management Commands

```bash
# Control services
~/bitcoin-bens-club/scripts/start.sh
~/bitcoin-bens-club/scripts/stop.sh
~/bitcoin-bens-club/scripts/status.sh

# Maintenance
~/bitcoin-bens-club/scripts/backup.sh
~/bitcoin-bens-club/scripts/update.sh

# Monitoring
tail -f /var/log/bitcoin-bens-monitor.log
htop
pm2 monit
```

## 💡 Features

### 🍔 Application Features
- **Member Registration & Login** (Email/Password)
- **$21 Annual Membership** or **1M $BBC Token Staking**
- **Multi-Currency Menu** (USD, BCH, BBC tokens)
- **Admin Dashboard** with full management
- **P2P Payment Integration** (Venmo, CashApp, Zelle, BCH)
- **Pump.fun Token Integration**
- **Affiliate System** ($3 commission per referral)
- **Order Management System**

### 🔒 Security & Access
- **Multiple Access Methods:**
  - Local network access
  - Internet access with SSL
  - VPN access (Tailscale/WireGuard)
  - Dynamic DNS for free domains

### 📱 Mobile Optimized
- Responsive design for all devices
- Touch-friendly interface
- Progressive Web App features

## 📋 Requirements

- **Hardware:** Raspberry Pi 5 (4GB+ RAM recommended)
- **OS:** Raspberry Pi OS (latest)
- **Network:** Internet connection
- **Access:** User with sudo privileges

## 🔧 Troubleshooting

All common issues and solutions are included in `docs/troubleshooting.md`

Quick diagnostics:
```bash
# System health check
./scripts/pi5-diagnostics.sh

# Service status
sudo systemctl status bbc-backend mongod nginx

# Check logs
tail -f ~/bitcoin-bens-club/logs/*.log
```

## 🌟 Production Ready

This package is designed for production use with:
- Automated backups and monitoring
- Security hardening and firewall
- SSL certificates and encrypted traffic
- High availability configuration
- Performance optimization for Pi5

---

**🍔 Ready to serve Bitcoin Burgers worldwide! 🚀**

For detailed setup instructions, see `INSTALL.md`
For network configuration, see `docs/network-setup.md`
For troubleshooting, see `docs/troubleshooting.md`
EOF

# Installation guide
cat > "$PACKAGE_DIR/INSTALL.md" << 'EOF'
# 📋 Installation Guide

## 🚀 Quick Install (Recommended)

1. **Extract the package:**
   ```bash
   tar -xzf bitcoin-bens-pi5-complete_*.tar.gz
   cd bitcoin-bens-pi5-complete_*/
   ```

2. **Run the installer:**
   ```bash
   chmod +x setup/install.sh
   ./setup/install.sh
   ```

3. **Follow interactive prompts for:**
   - Admin email and secure password
   - Domain name (or Dynamic DNS setup)
   - VPN configuration (Tailscale recommended)
   - SSL certificate setup
   - Network access options
   - Security and monitoring features

4. **Installation completes automatically!**

## 🎯 What Happens During Install

### Phase 1: System Setup (5-10 minutes)
- Updates Raspberry Pi OS
- Installs Node.js 18.x LTS
- Installs Python 3.11+ with virtual environment
- Installs MongoDB 7.0 with authentication
- Installs PM2, Nginx, and security tools

### Phase 2: Application Setup (3-5 minutes)
- Copies Bitcoin Ben's application code
- Installs all dependencies (Python + Node.js)
- Creates secure environment configuration
- Sets up database with admin user

### Phase 3: Network & Security (2-5 minutes)
- Configures firewall (UFW + Fail2Ban)
- Sets up SSL certificates (if domain provided)
- Configures VPN access (if selected)
- Sets up Dynamic DNS (if needed)
- Configures automatic port forwarding

### Phase 4: Monitoring & Services (1-2 minutes)
- Creates systemd services for auto-start
- Sets up system monitoring and alerts
- Configures automated backups
- Creates management scripts

## 🌐 Network Access Options

The installer offers multiple ways to access your Pi5:

### 1. Local Network Only
- Access via: `http://192.168.x.x:3000`
- Perfect for home/office use
- No additional configuration needed

### 2. Internet Access with Domain
- Requires: Your own domain name
- Gets: SSL certificate and secure HTTPS access
- Access via: `https://yourdomain.com`

### 3. Internet Access with Dynamic DNS
- Gets: Free subdomain (e.g., `bitcoinben.duckdns.org`)
- Includes: SSL certificate setup
- Perfect for home users without domain

### 4. VPN Access (Recommended)
- **Tailscale:** Easy setup, access from anywhere
- **WireGuard:** Full control, advanced users
- Most secure option for remote access

## 🔧 Post-Installation

After installation completes:

### 1. Verify Installation
```bash
# Check system status
~/bitcoin-bens-club/scripts/status.sh

# Test local access
curl http://localhost:3000
```

### 2. Access Your Application
- **Frontend:** Your Pi's IP address on port 3000
- **Admin Panel:** Add `?admin=true` to any URL
- **API Documentation:** Port 8001 `/docs` endpoint

### 3. First Admin Login
- Use the email and password you set during installation
- Go to `http://your-pi-ip:3000?admin=true`
- Complete any additional setup

## 🛠️ Management

### Daily Operations
```bash
# Check everything is running
~/bitcoin-bens-club/scripts/status.sh

# View system health
tail -f /var/log/bitcoin-bens-monitor.log

# Check recent activity
pm2 monit
```

### Maintenance
```bash
# Create backup before changes
~/bitcoin-bens-club/scripts/backup.sh

# Update system and application
~/bitcoin-bens-club/scripts/update.sh

# Restart services if needed
~/bitcoin-bens-club/scripts/start.sh
```

## 🚨 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check system resources
free -h
df -h /

# Check specific service
sudo systemctl status bbc-backend
sudo journalctl -u bbc-backend -f
```

**Can't access from other devices:**
```bash
# Check firewall
sudo ufw status

# Check if services are listening
sudo netstat -tlnp | grep ':3000\|:8001'

# Test local first
curl http://localhost:3000
```

**Database issues:**
```bash
# Check MongoDB
sudo systemctl status mongod
mongosh --eval "db.adminCommand('ismaster')"
```

### Recovery

If something goes wrong:
```bash
# Stop all services
~/bitcoin-bens-club/scripts/stop.sh

# Check logs
tail -f ~/bitcoin-bens-club/logs/*.log

# Restart everything
sudo reboot
```

### Get Help

1. **Check logs:** All services log to `~/bitcoin-bens-club/logs/`
2. **Run diagnostics:** `./scripts/pi5-diagnostics.sh`
3. **Review documentation:** See `docs/troubleshooting.md`
4. **Check service status:** `sudo systemctl status bbc-backend mongod nginx`

---

## 🎉 Success!

Once installation completes, you'll have:
- ✅ Production-ready Bitcoin Ben's Burger Bus Club
- ✅ Secure internet access (if configured)
- ✅ Automated backups and monitoring
- ✅ Easy management scripts
- ✅ Complete documentation

**Ready to serve Bitcoin Burgers! 🍔🚀**
EOF

# Quick reference
cat > "$PACKAGE_DIR/QUICK-REFERENCE.md" << 'EOF'
# 🚀 Bitcoin Ben's Quick Reference

## Installation
```bash
# One command install
tar -xzf bitcoin-bens-pi5-*.tar.gz && cd bitcoin-bens-pi5-*/ && ./setup/install.sh
```

## Access URLs
- **App:** `http://PI_IP:3000`
- **Admin:** `http://PI_IP:3000?admin=true`
- **API:** `http://PI_IP:8001`

## Essential Commands
```bash
# Services
~/bitcoin-bens-club/scripts/start.sh     # Start all
~/bitcoin-bens-club/scripts/stop.sh      # Stop all  
~/bitcoin-bens-club/scripts/status.sh    # Check status

# Maintenance
~/bitcoin-bens-club/scripts/backup.sh    # Create backup
~/bitcoin-bens-club/scripts/update.sh    # Update system
```

## Service Control
```bash
# Backend API
sudo systemctl start/stop/restart bbc-backend
sudo journalctl -u bbc-backend -f

# Frontend  
pm2 start/stop/restart bbc-frontend
pm2 logs bbc-frontend

# Database
sudo systemctl start/stop/restart mongod
```

## Monitoring
```bash
# System overview
htop

# Service monitoring  
pm2 monit

# Application logs
tail -f ~/bitcoin-bens-club/logs/*.log

# System monitoring
tail -f /var/log/bitcoin-bens-monitor.log
```

## Network & Security
```bash
# Firewall status
sudo ufw status

# Open ports
sudo netstat -tlnp

# SSL certificates  
sudo certbot certificates

# VPN status (if Tailscale)
tailscale status
```

## Emergency
```bash
# Full system restart
sudo reboot

# Check Pi5 health
vcgencmd measure_temp
vcgencmd get_throttled

# Diagnostic report
./scripts/pi5-diagnostics.sh
```

## Admin Panel
- **URL:** Add `?admin=true` to any page
- **Default:** `admin@bitcoinben.local` 
- **Features:** Member management, payments, system admin

## File Locations
```bash
# Application
~/bitcoin-bens-club/

# Logs  
~/bitcoin-bens-club/logs/
/var/log/bitcoin-bens-monitor.log

# Backups
~/bitcoin-bens-club/backups/

# Configuration
~/bitcoin-bens-club/backend/.env
~/bitcoin-bens-club/frontend/.env
```
EOF

echo "📋 Creating management tools..."
# Copy tools and scripts
cp -r scripts/* "$PACKAGE_DIR/scripts/" 2>/dev/null || true

# Create final installer script
cat > "$PACKAGE_DIR/setup/install.sh" << 'EOF'
#!/bin/bash
# Main installer - chooses between basic and enhanced
echo "🍔 Bitcoin Ben's Burger Bus Club - Pi5 Installer"
echo ""
echo "Choose installation type:"
echo "1) Enhanced Setup (Recommended) - Full features with internet access"
echo "2) Basic Setup - Local network only"
echo "3) Quick Setup - Fastest installation with defaults"
echo ""
read -p "Enter choice (1-3): " INSTALL_TYPE

case $INSTALL_TYPE in
    1)
        echo "🚀 Running Enhanced Setup..."
        ./install-enhanced.sh 2>/dev/null || ./setup-pi5.sh
        ;;
    2) 
        echo "🔧 Running Basic Setup..."
        ./setup-pi5.sh
        ;;
    3)
        echo "⚡ Running Quick Setup..."
        ./quick-deploy.sh 2>/dev/null || ./setup-pi5.sh
        ;;
    *)
        echo "❌ Invalid choice. Running basic setup..."
        ./setup-pi5.sh
        ;;
esac
EOF

chmod +x "$PACKAGE_DIR/setup/install.sh"

# Create package info
cat > "$PACKAGE_DIR/PACKAGE-INFO.txt" << EOF
Bitcoin Ben's Burger Bus Club - Complete Pi5 Package
===================================================

Created: $(date)
Version: 1.0.0
Target: Raspberry Pi 5

Package Contents:
- Complete application source code
- Automated installation scripts  
- Internet access configuration
- SSL/VPN setup tools
- Security hardening
- System monitoring
- Management utilities
- Comprehensive documentation

Installation:
./setup/install.sh

Features:
✅ One-command installation
✅ Production-ready deployment  
✅ Multi-currency payment system
✅ Admin dashboard
✅ Internet access with SSL
✅ VPN support (Tailscale/WireGuard)
✅ Automated backups
✅ System monitoring
✅ Security hardening

Total Files: $(find "$PACKAGE_DIR" -type f | wc -l)
Package Size: $(du -sh "$PACKAGE_DIR" | cut -f1)

Ready to serve Bitcoin Burgers worldwide! 🍔🚀
EOF

echo "🗜️ Creating compressed package..."
tar -czf "${PACKAGE_DIR}.tar.gz" "$PACKAGE_DIR"

# Create checksums
sha256sum "${PACKAGE_DIR}.tar.gz" > "${PACKAGE_DIR}.sha256"
md5sum "${PACKAGE_DIR}.tar.gz" > "${PACKAGE_DIR}.md5"

echo ""
echo "✅ Complete Bitcoin Ben's Pi5 Package Created!"
echo "=============================================="
echo ""
echo "📦 Package: ${PACKAGE_DIR}.tar.gz"
echo "📏 Size: $(ls -lh "${PACKAGE_DIR}.tar.gz" | awk '{print $5}')"  
echo "📁 Files: $(tar -tzf "${PACKAGE_DIR}.tar.gz" | wc -l) files"
echo "🔐 SHA256: $(head -c 16 "${PACKAGE_DIR}.sha256")..."
echo ""
echo "📋 Transfer to Pi5:"
echo "   scp ${PACKAGE_DIR}.tar.gz pi@your-pi-ip:~/"
echo ""
echo "🚀 Install on Pi5:"
echo "   tar -xzf ${PACKAGE_DIR}.tar.gz"  
echo "   cd ${PACKAGE_DIR}/"
echo "   ./setup/install.sh"
echo ""
echo "🎯 One-Command Web Install:"
echo "   curl -sSL bitcoin-bens.com/install | bash"
echo ""
echo "🍔 Ready to deploy Bitcoin Ben's worldwide!"

# Cleanup
rm -rf "$PACKAGE_DIR"