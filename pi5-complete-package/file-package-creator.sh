#!/bin/bash

# Bitcoin Ben's Burger Bus Club - File Package Creator
# Creates a complete, transferable package for Pi5 installation

set -e

PACKAGE_NAME="bitcoin-bens-pi5-complete"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_DIR="${PACKAGE_NAME}_${TIMESTAMP}"

echo "📦 Creating Bitcoin Ben's Pi5 Complete Package..."
echo "================================================"

# Create package directory structure
mkdir -p "$PACKAGE_DIR"/{setup,app-source,docs,scripts}

echo "📁 Copying setup files..."

# Copy main installation files (these should exist in pi5-setup/)
cp pi5-setup/setup-pi5.sh "$PACKAGE_DIR/setup/"
cp pi5-setup/copy-files.sh "$PACKAGE_DIR/setup/"
cp pi5-setup/README.md "$PACKAGE_DIR/"
cp pi5-setup/network-setup.md "$PACKAGE_DIR/docs/"
cp pi5-setup/troubleshooting.md "$PACKAGE_DIR/docs/"

# Copy the enhanced installer
cp install.sh "$PACKAGE_DIR/setup/install-enhanced.sh"
cp quick-deploy.sh "$PACKAGE_DIR/setup/"

echo "📁 Copying application source code..."

# Copy backend files (excluding sensitive data)
if [ -d "../backend" ]; then
    cp -r ../backend "$PACKAGE_DIR/app-source/"
    
    # Remove sensitive files
    rm -f "$PACKAGE_DIR/app-source/backend/.env"
    rm -rf "$PACKAGE_DIR/app-source/backend/__pycache__"
    rm -rf "$PACKAGE_DIR/app-source/backend/*.pyc"
    rm -rf "$PACKAGE_DIR/app-source/backend/venv"
    
    # Create template .env
    cat > "$PACKAGE_DIR/app-source/backend/.env.template" << 'EOF'
# MongoDB Configuration (will be auto-generated during setup)
MONGO_URL="mongodb://localhost:27017/bitcoin_bens_club"
DB_NAME="bitcoin_bens_club"

# Server Configuration
HOST=0.0.0.0
PORT=8001

# Security (will be auto-generated)
JWT_SECRET_KEY=""
ADMIN_EMAIL=""
ADMIN_PASSWORD=""

# BCH Configuration
BCH_RECEIVING_ADDRESS="bitcoincash:qph0duvh0zn0r2um7znh8gx20p50dr3ycc5lcp0sc4"

# Pump.fun Token Configuration
PUMP_FUN_TOKEN_ADDRESS="mWusXdRfsYAoFtYdaDcf8tmG7hnRNvnVc2TuvNEpump"
EOF
fi

# Copy frontend files
if [ -d "../frontend" ]; then
    cp -r ../frontend "$PACKAGE_DIR/app-source/"
    
    # Remove build artifacts
    rm -rf "$PACKAGE_DIR/app-source/frontend/node_modules"
    rm -rf "$PACKAGE_DIR/app-source/frontend/build"
    rm -rf "$PACKAGE_DIR/app-source/frontend/.env"
    rm -f "$PACKAGE_DIR/app-source/frontend/yarn.lock"
    rm -f "$PACKAGE_DIR/app-source/frontend/package-lock.json"
    
    # Create template .env
    cat > "$PACKAGE_DIR/app-source/frontend/.env.template" << 'EOF'
# Backend API Configuration (will be auto-configured)
REACT_APP_BACKEND_URL=http://localhost:8001

# Build Configuration
GENERATE_SOURCEMAP=false
REACT_APP_VERSION=1.0.0
EOF
fi

echo "📄 Creating documentation..."

# Create comprehensive README
cat > "$PACKAGE_DIR/README.md" << 'EOF'
# Bitcoin Ben's Burger Bus Club - Complete Pi5 Package

## 🎯 Quick Start (One Command Install)

For the fastest setup, run this single command on your Pi5:

```bash
curl -sSL https://raw.githubusercontent.com/bitcoin-bens/pi5-setup/main/quick-deploy.sh | bash
```

OR download this package and run:

```bash
cd setup/
chmod +x install-enhanced.sh
sudo ./install-enhanced.sh
```

## 📦 What's Included

### Complete Application Stack
- ✅ Bitcoin Ben's Burger Bus Club (Frontend + Backend)
- ✅ MongoDB 7.0 with authentication
- ✅ Node.js 18.x LTS + Python 3.11+
- ✅ PM2 Process Manager
- ✅ Nginx reverse proxy

### Internet Access & Security
- ✅ SSL certificates (Let's Encrypt)
- ✅ VPN access (Tailscale or WireGuard)
- ✅ Enhanced firewall (UFW + Fail2Ban)
- ✅ Dynamic DNS support (DuckDNS)
- ✅ Automatic port forwarding (UPnP)

### Monitoring & Management
- ✅ System monitoring dashboard
- ✅ Automated backups
- ✅ Health checks & alerts
- ✅ Easy management scripts
- ✅ Log aggregation

## 🚀 Installation Options

### Option 1: Enhanced Interactive Setup (Recommended)
```bash
cd setup/
./install-enhanced.sh
```

Features:
- Interactive configuration
- SSL certificate setup
- VPN configuration
- Internet access setup
- Security hardening
- System monitoring

### Option 2: Basic Setup
```bash
cd setup/
./setup-pi5.sh
```

Features:
- Basic installation
- Local network access only
- Manual configuration required

### Option 3: Manual Step-by-Step
1. Run `setup-pi5.sh` for basic installation
2. Copy application files with `copy-files.sh`
3. Configure network access using `docs/network-setup.md`

## 📋 Requirements

- Raspberry Pi 5 (4GB+ RAM recommended)
- Raspberry Pi OS (latest)
- Internet connection
- User account with sudo access
- Router with port forwarding capability (for internet access)

## 🌐 Access Your Application

After installation:

**Local Access:**
- Frontend: `http://your-pi-ip:3000`
- Admin Panel: `http://your-pi-ip:3000?admin=true`
- Backend API: `http://your-pi-ip:8001`

**Internet Access (if configured):**
- Frontend: `https://your-domain.com`
- Admin Panel: `https://your-domain.com?admin=true`

**VPN Access (if configured):**
- Tailscale: `http://tailscale-ip:3000`
- WireGuard: Use client configuration provided

## 🛠️ Management Commands

```bash
# Start services
~/bitcoin-bens-club/scripts/start.sh

# Check status
~/bitcoin-bens-club/scripts/status.sh

# Stop services
~/bitcoin-bens-club/scripts/stop.sh

# Create backup
~/bitcoin-bens-club/scripts/backup.sh

# Update application
~/bitcoin-bens-club/scripts/update.sh
```

## 🔧 Troubleshooting

See `docs/troubleshooting.md` for common issues and solutions.

For support, check the logs:
```bash
# Application logs
tail -f ~/bitcoin-bens-club/logs/*.log

# System logs
sudo journalctl -f -u bbc-backend
sudo journalctl -f -u mongod

# System monitoring
tail -f /var/log/bitcoin-bens-monitor.log
```

## 🔒 Security Features

- MongoDB authentication enabled
- UFW firewall configured
- Fail2Ban protection for SSH and web services
- SSL/TLS encryption for web traffic
- Regular security updates
- VPN access options
- Secure admin panel access

## 📊 Monitoring

The system includes comprehensive monitoring:
- CPU, memory, and disk usage tracking
- Service health monitoring
- Temperature monitoring (Pi5 specific)
- Automated alerts for critical issues
- Web-based monitoring dashboard
- Log aggregation and rotation

## 🔄 Updates

The application includes an automatic update system:
```bash
~/bitcoin-bens-club/scripts/update.sh
```

This will:
- Stop services safely
- Create automatic backup
- Update system packages
- Update application dependencies
- Restart services
- Verify functionality

## 🌍 Internet Access Setup

The package includes multiple options for internet access:

1. **Router Port Forwarding** (Traditional)
2. **Dynamic DNS** (Free domain names)
3. **VPN Access** (Secure remote access)
4. **Cloudflare Tunnels** (Enterprise-grade)

See `docs/network-setup.md` for detailed instructions.

---

🍔 **Ready to serve Bitcoin Burgers to the world!** 🚀
EOF

# Create installation guide
cat > "$PACKAGE_DIR/INSTALL.md" << 'EOF'
# Installation Guide

## Quick Install (Recommended)

1. **Copy this package to your Pi5**
2. **Extract and run:**
   ```bash
   tar -xzf bitcoin-bens-pi5-complete_*.tar.gz
   cd bitcoin-bens-pi5-complete_*/
   chmod +x setup/install-enhanced.sh
   ./setup/install-enhanced.sh
   ```

3. **Follow the interactive prompts for:**
   - Domain name setup
   - Admin credentials
   - VPN configuration
   - SSL certificate setup
   - Network access options

4. **Copy your application files:**
   ```bash
   cp -r app-source/* ~/bitcoin-bens-club/
   cd ~/bitcoin-bens-club/
   ./complete-setup.sh
   ```

5. **Start the application:**
   ```bash
   ./scripts/start.sh
   ```

## Manual Install

If you prefer step-by-step installation:

1. **Basic system setup:**
   ```bash
   ./setup/setup-pi5.sh
   ```

2. **Copy application files:**
   ```bash
   ./setup/copy-files.sh
   ```

3. **Configure network access:**
   - Follow instructions in `docs/network-setup.md`
   - Configure your router for port forwarding
   - Setup SSL certificates if needed

4. **Start services:**
   ```bash
   ~/bitcoin-bens-club/scripts/start.sh
   ```

## Verification

After installation, verify everything is working:

```bash
# Check system status
~/bitcoin-bens-club/scripts/status.sh

# Test local access
curl http://localhost:3000

# Test API
curl http://localhost:8001/api/

# Check logs
tail -f ~/bitcoin-bens-club/logs/*.log
```

## Troubleshooting

If you encounter issues:

1. **Check the troubleshooting guide:** `docs/troubleshooting.md`
2. **Review installation logs:** `~/bitcoin-bens-club/install.log`
3. **Check service status:** `sudo systemctl status bbc-backend mongod`
4. **Verify network connectivity:** `ping google.com`

## Support

For additional support:
- Review all documentation in the `docs/` folder
- Check the application logs
- Verify all prerequisites are met
- Ensure proper network configuration

---

Happy Bitcoin Burger serving! 🍔
EOF

# Create quick reference card
cat > "$PACKAGE_DIR/QUICK-REFERENCE.md" << 'EOF'
# Bitcoin Ben's Quick Reference

## 🚀 One-Command Install
```bash
cd setup/ && ./install-enhanced.sh
```

## 📱 Access URLs
- **Frontend:** http://PI_IP:3000
- **Admin:** http://PI_IP:3000?admin=true  
- **API:** http://PI_IP:8001

## 🛠️ Essential Commands
```bash
# Start all services
~/bitcoin-bens-club/scripts/start.sh

# Check status
~/bitcoin-bens-club/scripts/status.sh

# View logs
tail -f ~/bitcoin-bens-club/logs/*.log

# Create backup
~/bitcoin-bens-club/scripts/backup.sh
```

## 🔧 Service Management
```bash
# Backend service
sudo systemctl start/stop/restart bbc-backend

# Frontend (PM2)
pm2 start/stop/restart bbc-frontend

# Database
sudo systemctl start/stop/restart mongod
```

## 🌐 Network Setup
- **Port Forward:** 3000, 8001, 80, 443
- **Firewall:** `sudo ufw status`
- **SSL Cert:** `sudo certbot certificates`

## 🔒 Admin Access
- **Default:** admin@bitcoinben.local
- **Password:** Set during installation
- **Panel:** Add `?admin=true` to any URL

## 📊 Monitoring
```bash
# System stats
htop

# Process monitor
pm2 monit

# Service logs
sudo journalctl -f -u bbc-backend
```

## 🆘 Emergency
```bash
# Stop everything
~/bitcoin-bens-club/scripts/stop.sh

# Full restart
sudo reboot

# Check Pi5 temp
vcgencmd measure_temp
```
EOF

echo "🔧 Creating utility scripts..."

# Create a Pi5 diagnostic script
cat > "$PACKAGE_DIR/scripts/pi5-diagnostics.sh" << 'EOF'
#!/bin/bash
echo "🔍 Pi5 Diagnostic Report"
echo "======================="

echo "Hardware:"
echo "  Model: $(cat /proc/cpuinfo | grep Model | head -1 | cut -d: -f2)"
echo "  Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "  CPU Temp: $(vcgencmd measure_temp)"
echo "  Throttling: $(vcgencmd get_throttled)"

echo -e "\nNetwork:"
echo "  Local IP: $(hostname -I | awk '{print $1}')"
echo "  External IP: $(curl -s ifconfig.me 2>/dev/null || echo "Not available")"
echo "  DNS: $(cat /etc/resolv.conf | grep nameserver | head -1 | awk '{print $2}')"

echo -e "\nStorage:"
df -h /

echo -e "\nServices:"
systemctl is-active mongod nginx ufw fail2ban 2>/dev/null || echo "Some services not installed"

echo -e "\nPorts:"
sudo netstat -tlnp | grep ':3000\|:8001\|:80\|:443' 2>/dev/null || echo "No services listening"
EOF

chmod +x "$PACKAGE_DIR/scripts/pi5-diagnostics.sh"

# Create backup/restore scripts
cat > "$PACKAGE_DIR/scripts/backup-restore.sh" << 'EOF'
#!/bin/bash

backup() {
    echo "📦 Creating full backup..."
    BACKUP_NAME="bitcoin-bens-backup-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "/tmp/$BACKUP_NAME"
    
    # Backup application
    cp -r ~/bitcoin-bens-club "/tmp/$BACKUP_NAME/"
    
    # Backup MongoDB
    mongodump --db bitcoin_bens_club --out "/tmp/$BACKUP_NAME/mongodb"
    
    # Create archive
    cd /tmp
    tar -czf "$HOME/${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
    rm -rf "/tmp/$BACKUP_NAME"
    
    echo "✅ Backup created: $HOME/${BACKUP_NAME}.tar.gz"
}

restore() {
    echo "📥 Restoring from backup..."
    read -p "Enter backup file path: " BACKUP_FILE
    
    if [[ ! -f "$BACKUP_FILE" ]]; then
        echo "❌ Backup file not found: $BACKUP_FILE"
        exit 1
    fi
    
    # Stop services
    ~/bitcoin-bens-club/scripts/stop.sh
    
    # Extract backup
    cd /tmp
    tar -xzf "$BACKUP_FILE"
    
    # Restore application
    BACKUP_DIR=$(basename "$BACKUP_FILE" .tar.gz)
    cp -r "/tmp/$BACKUP_DIR/bitcoin-bens-club"/* ~/bitcoin-bens-club/
    
    # Restore MongoDB
    mongorestore "/tmp/$BACKUP_DIR/mongodb"
    
    # Cleanup
    rm -rf "/tmp/$BACKUP_DIR"
    
    # Restart services
    ~/bitcoin-bens-club/scripts/start.sh
    
    echo "✅ Restore completed!"
}

case "$1" in
    backup) backup ;;
    restore) restore ;;
    *) 
        echo "Usage: $0 {backup|restore}"
        echo "  backup  - Create full system backup"
        echo "  restore - Restore from backup file"
        ;;
esac
EOF

chmod +x "$PACKAGE_DIR/scripts/backup-restore.sh"

echo "📚 Finalizing package..."

# Create package manifest
cat > "$PACKAGE_DIR/MANIFEST.txt" << EOF
Bitcoin Ben's Burger Bus Club - Pi5 Complete Package
Generated: $(date)
Version: 1.0.0

Contents:
- setup/install-enhanced.sh    (Enhanced interactive installer)
- setup/setup-pi5.sh          (Basic Pi5 setup script)
- setup/copy-files.sh          (File copying utility)
- setup/quick-deploy.sh        (One-command web installer)
- app-source/backend/          (Python FastAPI backend)
- app-source/frontend/         (React frontend application)
- docs/network-setup.md        (Internet access configuration)
- docs/troubleshooting.md      (Common issues and solutions)
- scripts/pi5-diagnostics.sh   (System diagnostic tool)
- scripts/backup-restore.sh    (Backup and restore utilities)
- README.md                    (Complete setup guide)
- INSTALL.md                   (Step-by-step installation)
- QUICK-REFERENCE.md           (Command reference)

Installation:
1. Extract package on Pi5
2. Run setup/install-enhanced.sh
3. Follow interactive prompts
4. Copy application files
5. Start services

Support:
- All documentation included in docs/ folder
- Diagnostic tools in scripts/ folder
- Log files will be in ~/bitcoin-bens-club/logs/

Total files: $(find "$PACKAGE_DIR" -type f | wc -l)
Package size: $(du -sh "$PACKAGE_DIR" | cut -f1)
EOF

echo "🗜️  Creating compressed package..."

# Create compressed package
tar -czf "${PACKAGE_DIR}.tar.gz" "$PACKAGE_DIR"

# Create checksums
sha256sum "${PACKAGE_DIR}.tar.gz" > "${PACKAGE_DIR}.sha256"
md5sum "${PACKAGE_DIR}.tar.gz" > "${PACKAGE_DIR}.md5"

echo "✅ Package creation completed!"
echo ""
echo "📦 Package Details:"
echo "   Name: ${PACKAGE_DIR}.tar.gz"
echo "   Size: $(ls -lh "${PACKAGE_DIR}.tar.gz" | awk '{print $5}')"
echo "   Files: $(tar -tzf "${PACKAGE_DIR}.tar.gz" | wc -l) files"
echo "   SHA256: $(cat "${PACKAGE_DIR}.sha256" | cut -d' ' -f1)"
echo ""
echo "📋 Transfer to Pi5:"
echo "   scp ${PACKAGE_DIR}.tar.gz pi@your-pi-ip:~/"
echo ""
echo "🚀 Install on Pi5:"
echo "   tar -xzf ${PACKAGE_DIR}.tar.gz"
echo "   cd ${PACKAGE_DIR}/"
echo "   ./setup/install-enhanced.sh"
echo ""
echo "🍔 Ready to deploy Bitcoin Ben's Burger Bus Club!"

# Cleanup
rm -rf "$PACKAGE_DIR"
EOF
      chmod +x "$PACKAGE_DIR/scripts/backup-restore.sh"
    </file>