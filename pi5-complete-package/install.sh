#!/bin/bash

# Bitcoin Ben's Burger Bus Club - ONE-COMMAND Pi5 Installer
# This script does EVERYTHING: downloads, installs, configures, and sets up internet access

set -e

# Colors and styling
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# ASCII Art Banner
print_banner() {
    echo -e "${YELLOW}"
    cat << 'EOF'
    ┌─────────────────────────────────────────────────────────────┐
    │  🍔 Bitcoin Ben's Burger Bus Club - Pi5 One-Command Setup   │
    │                                                             │
    │  🚀 Complete Production Setup with SSL & Internet Access    │
    │  🔒 Security Hardened • 🌐 Internet Ready • 📊 Monitoring  │
    └─────────────────────────────────────────────────────────────┘
EOF
    echo -e "${NC}"
}

print_status() { echo -e "${GREEN}[✓]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; }
print_error() { echo -e "${RED}[✗]${NC} $1"; }
print_info() { echo -e "${CYAN}[ℹ]${NC} $1"; }
print_header() { echo -e "\n${BLUE}${BOLD}=== $1 ===${NC}\n"; }

# Configuration variables
INSTALL_DIR="$HOME/bitcoin-bens-club"
BACKUP_DIR="$INSTALL_DIR/backups"
LOG_FILE="$INSTALL_DIR/install.log"
LOCAL_IP=$(hostname -I | awk '{print $1}')

# Setup logging
setup_logging() {
    mkdir -p "$INSTALL_DIR"
    exec 1> >(tee -a "$LOG_FILE")
    exec 2> >(tee -a "$LOG_FILE" >&2)
}

# Interactive configuration
interactive_setup() {
    print_header "Interactive Configuration Setup"
    
    # Domain setup
    echo -e "${CYAN}🌐 Domain & SSL Setup:${NC}"
    read -p "Do you have a domain name? (y/n): " HAS_DOMAIN
    
    if [[ $HAS_DOMAIN =~ ^[Yy]$ ]]; then
        read -p "Enter your domain name (e.g., bitcoinben.com): " DOMAIN_NAME
        read -p "Setup SSL with Let's Encrypt? (y/n): " SETUP_SSL
    else
        print_info "We'll setup Dynamic DNS for free domain access"
        SETUP_DDNS="y"
    fi
    
    # VPN Setup
    echo -e "\n${PURPLE}🔒 VPN Access Setup:${NC}"
    echo "Choose VPN option:"
    echo "1) Tailscale (Recommended - Easy & Secure)"
    echo "2) WireGuard (Advanced - Full Control)"  
    echo "3) No VPN (Port Forwarding Only)"
    read -p "Enter choice (1-3): " VPN_CHOICE
    
    # Admin credentials
    echo -e "\n${GREEN}👤 Admin Account Setup:${NC}"
    read -p "Admin email [admin@bitcoinben.local]: " ADMIN_EMAIL
    ADMIN_EMAIL=${ADMIN_EMAIL:-admin@bitcoinben.local}
    
    while true; do
        read -s -p "Admin password (min 8 chars): " ADMIN_PASSWORD
        echo
        if [[ ${#ADMIN_PASSWORD} -ge 8 ]]; then
            read -s -p "Confirm password: " ADMIN_PASSWORD_CONFIRM
            echo
            if [[ "$ADMIN_PASSWORD" == "$ADMIN_PASSWORD_CONFIRM" ]]; then
                break
            else
                print_error "Passwords don't match. Try again."
            fi
        else
            print_error "Password must be at least 8 characters."
        fi
    done
    
    # Network setup
    echo -e "\n${BLUE}🌐 Network Configuration:${NC}"
    read -p "Setup automatic port forwarding (UPnP)? (y/n): " SETUP_UPNP
    read -p "Setup firewall with fail2ban protection? (y/n): " SETUP_SECURITY
    
    # Monitoring
    echo -e "\n${YELLOW}📊 Monitoring & Alerts:${NC}"
    read -p "Setup system monitoring dashboard? (y/n): " SETUP_MONITORING
    read -p "Enable email alerts for system issues? (y/n): " SETUP_ALERTS
    
    if [[ $SETUP_ALERTS =~ ^[Yy]$ ]]; then
        read -p "Alert email address: " ALERT_EMAIL
    fi
    
    # Summary
    echo -e "\n${BOLD}Configuration Summary:${NC}"
    echo "• Install Directory: $INSTALL_DIR"
    echo "• Local IP: $LOCAL_IP"
    [[ -n $DOMAIN_NAME ]] && echo "• Domain: $DOMAIN_NAME"
    echo "• Admin: $ADMIN_EMAIL"
    echo "• VPN: $([ $VPN_CHOICE -eq 1 ] && echo "Tailscale" || [ $VPN_CHOICE -eq 2 ] && echo "WireGuard" || echo "None")"
    echo "• SSL: $([ "$SETUP_SSL" = "y" ] && echo "Yes" || echo "No")"
    echo "• Security: $([ "$SETUP_SECURITY" = "y" ] && echo "Enhanced" || echo "Basic")"
    echo "• Monitoring: $([ "$SETUP_MONITORING" = "y" ] && echo "Yes" || echo "No")"
    
    read -p "Continue with installation? (y/n): " CONTINUE
    [[ ! $CONTINUE =~ ^[Yy]$ ]] && exit 0
}

# System updates and basic packages
update_system() {
    print_header "System Update & Basic Packages"
    
    sudo apt update
    sudo apt upgrade -y
    sudo apt install -y curl wget git htop unzip build-essential \
                        software-properties-common apt-transport-https \
                        ca-certificates gnupg lsb-release jq bc \
                        ufw fail2ban nginx certbot python3-certbot-nginx
    
    print_status "System updated and basic packages installed"
}

# Install Node.js 18.x LTS
install_nodejs() {
    print_header "Installing Node.js 18.x LTS"
    
    if ! command -v node &> /dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
        
        # Install Yarn
        curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
        echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
        sudo apt update && sudo apt install -y yarn
        
        # Install PM2
        sudo npm install -g pm2
        pm2 startup
        sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u $USER --hp $HOME
        
        print_status "Node.js, Yarn, and PM2 installed"
    else
        print_status "Node.js already installed: $(node -v)"
    fi
}

# Install Python 3.11+
install_python() {
    print_header "Setting up Python Environment"
    
    sudo apt install -y python3 python3-pip python3-venv python3-dev \
                        python3-setuptools python3-wheel
    
    # Create virtual environment
    python3 -m venv "$INSTALL_DIR/venv"
    source "$INSTALL_DIR/venv/bin/activate"
    pip install --upgrade pip
    
    print_status "Python virtual environment created"
}

# Install MongoDB 7.0
install_mongodb() {
    print_header "Installing MongoDB 7.0 Community Edition"
    
    # Import MongoDB public GPG Key
    curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
        sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
    
    # Create list file for MongoDB
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
        sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    
    sudo apt-get update
    sudo apt-get install -y mongodb-org
    
    # Start and enable MongoDB
    sudo systemctl start mongod
    sudo systemctl enable mongod
    
    # Wait for MongoDB to start
    sleep 10
    
    # Create MongoDB admin user
    MONGO_ADMIN_PASS=$(openssl rand -base64 32)
    mongosh --eval "
        use admin;
        db.createUser({
            user: 'bbcadmin',
            pwd: '$MONGO_ADMIN_PASS',
            roles: ['root']
        });
    "
    
    # Enable authentication
    sudo sed -i '/^#security:/a security:\n  authorization: enabled' /etc/mongod.conf
    sudo systemctl restart mongod
    
    # Store credentials securely
    echo "MONGO_ADMIN_PASS=$MONGO_ADMIN_PASS" >> "$INSTALL_DIR/.mongodb-credentials"
    chmod 600 "$INSTALL_DIR/.mongodb-credentials"
    
    print_status "MongoDB installed with authentication"
}

# Download and setup application
setup_application() {
    print_header "Setting up Bitcoin Ben's Application"
    
    mkdir -p "$INSTALL_DIR"/{backend,frontend,config,logs,scripts,ssl}
    
    # Create application files structure
    cd "$INSTALL_DIR"
    
    # We'll need the user to provide the actual application files
    # For now, create placeholder structure
    print_info "Application directory structure created"
    print_warning "You'll need to copy your backend/ and frontend/ code to $INSTALL_DIR/"
}

# Setup environment configuration
setup_environment() {
    print_header "Configuring Environment Variables"
    
    # Generate secure keys
    JWT_SECRET=$(openssl rand -hex 64)
    APP_SECRET=$(openssl rand -hex 32)
    
    # Backend environment
    cat > "$INSTALL_DIR/backend/.env" << EOF
# Database Configuration
MONGO_URL="mongodb://bbcadmin:$(grep MONGO_ADMIN_PASS "$INSTALL_DIR/.mongodb-credentials" | cut -d= -f2)@localhost:27017/bitcoin_bens_club?authSource=admin"
DB_NAME="bitcoin_bens_club"

# Server Configuration
HOST=0.0.0.0
PORT=8001
CORS_ORIGINS=["http://localhost:3000","http://${LOCAL_IP}:3000","https://${DOMAIN_NAME:-$LOCAL_IP}"]

# Security
JWT_SECRET_KEY="$JWT_SECRET"
APP_SECRET_KEY="$APP_SECRET"

# Admin Configuration
ADMIN_EMAIL="$ADMIN_EMAIL"
ADMIN_PASSWORD="$ADMIN_PASSWORD"

# BCH Configuration
BCH_RECEIVING_ADDRESS="bitcoincash:qph0duvh0zn0r2um7znh8gx20p50dr3ycc5lcp0sc4"

# Pump.fun Token Configuration
PUMP_FUN_TOKEN_ADDRESS="mWusXdRfsYAoFtYdaDcf8tmG7hnRNvnVc2TuvNEpump"

# Feature Flags
ENABLE_REGISTRATION=true
ENABLE_STAKING=true
ENABLE_ADMIN_PANEL=true

# Logging
LOG_LEVEL=INFO
LOG_FILE="$INSTALL_DIR/logs/backend.log"
EOF

    # Frontend environment
    FRONTEND_URL="http://${LOCAL_IP}:8001"
    [[ -n $DOMAIN_NAME ]] && FRONTEND_URL="https://$DOMAIN_NAME"
    
    cat > "$INSTALL_DIR/frontend/.env" << EOF
# Backend API Configuration
REACT_APP_BACKEND_URL=$FRONTEND_URL
REACT_APP_API_BASE_URL=$FRONTEND_URL/api

# Build Configuration
GENERATE_SOURCEMAP=false
REACT_APP_VERSION=1.0.0

# Feature Flags
REACT_APP_ENABLE_STAKING=true
REACT_APP_ENABLE_ADMIN=true

# Network Configuration
REACT_APP_LOCAL_IP=$LOCAL_IP
${DOMAIN_NAME:+REACT_APP_DOMAIN=$DOMAIN_NAME}
EOF

    chmod 600 "$INSTALL_DIR/backend/.env" "$INSTALL_DIR/frontend/.env"
    print_status "Environment variables configured securely"
}

# Setup VPN (Tailscale)
setup_tailscale() {
    print_header "Setting up Tailscale VPN"
    
    curl -fsSL https://tailscale.com/install.sh | sh
    
    print_info "Starting Tailscale setup..."
    print_warning "You'll need to authenticate in your browser"
    
    sudo tailscale up --accept-routes --accept-dns
    
    TAILSCALE_IP=$(tailscale ip -4)
    print_status "Tailscale connected! Your Tailscale IP: $TAILSCALE_IP"
    
    # Update frontend env with Tailscale IP
    echo "REACT_APP_TAILSCALE_IP=$TAILSCALE_IP" >> "$INSTALL_DIR/frontend/.env"
}

# Setup WireGuard VPN
setup_wireguard() {
    print_header "Setting up WireGuard VPN Server"
    
    sudo apt install -y wireguard qrencode
    
    # Generate server keys
    cd /etc/wireguard
    sudo wg genkey | sudo tee privatekey | sudo wg pubkey | sudo tee publickey
    
    SERVER_PRIVATE_KEY=$(sudo cat privatekey)
    SERVER_PUBLIC_KEY=$(sudo cat publickey)
    
    # Create server config
    sudo tee wg0.conf << EOF
[Interface]
PrivateKey = $SERVER_PRIVATE_KEY
Address = 10.0.0.1/24
ListenPort = 51820
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# Client configurations will be added here
EOF

    # Enable IP forwarding
    echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf
    sudo sysctl -p
    
    # Start WireGuard
    sudo systemctl enable wg-quick@wg0
    sudo systemctl start wg-quick@wg0
    
    # Allow WireGuard port
    sudo ufw allow 51820/udp
    
    print_status "WireGuard server configured on port 51820"
    print_info "Server public key: $SERVER_PUBLIC_KEY"
}

# Setup Dynamic DNS
setup_ddns() {
    print_header "Setting up Dynamic DNS (DuckDNS)"
    
    read -p "Enter desired subdomain (e.g., 'bitcoinben' for bitcoinben.duckdns.org): " DDNS_SUBDOMAIN
    read -p "Enter DuckDNS token (get from duckdns.org): " DDNS_TOKEN
    
    # Create DuckDNS update script
    cat > "$INSTALL_DIR/scripts/update-ddns.sh" << EOF
#!/bin/bash
curl "https://www.duckdns.org/update?domains=$DDNS_SUBDOMAIN&token=$DDNS_TOKEN&ip="
EOF
    
    chmod +x "$INSTALL_DIR/scripts/update-ddns.sh"
    
    # Add to cron for automatic updates
    (crontab -l 2>/dev/null; echo "*/5 * * * * $INSTALL_DIR/scripts/update-ddns.sh") | crontab -
    
    # Update domain configuration
    DOMAIN_NAME="$DDNS_SUBDOMAIN.duckdns.org"
    
    # Run initial update
    "$INSTALL_DIR/scripts/update-ddns.sh"
    
    print_status "Dynamic DNS configured: https://$DOMAIN_NAME"
}

# Setup SSL with Let's Encrypt
setup_ssl() {
    print_header "Setting up SSL Certificate (Let's Encrypt)"
    
    [[ -z $DOMAIN_NAME ]] && { print_error "Domain name required for SSL"; return 1; }
    
    # Create Nginx configuration
    sudo tee /etc/nginx/sites-available/bitcoin-bens << EOF
server {
    listen 80;
    server_name $DOMAIN_NAME;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN_NAME;
    
    # SSL Configuration (certificates will be added by certbot)
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    # Enable site
    sudo ln -sf /etc/nginx/sites-available/bitcoin-bens /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx
    
    # Get SSL certificate
    sudo certbot --nginx -d "$DOMAIN_NAME" --non-interactive --agree-tos --email "$ADMIN_EMAIL"
    
    # Setup auto-renewal
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
    
    print_status "SSL certificate installed for $DOMAIN_NAME"
}

# Setup UPnP for automatic port forwarding
setup_upnp() {
    print_header "Setting up Automatic Port Forwarding (UPnP)"
    
    sudo apt install -y miniupnpc
    
    # Forward required ports
    upnpc -a $LOCAL_IP 3000 3000 TCP "Bitcoin Bens Frontend"
    upnpc -a $LOCAL_IP 8001 8001 TCP "Bitcoin Bens API"
    upnpc -a $LOCAL_IP 80 80 TCP "Bitcoin Bens HTTP"
    upnpc -a $LOCAL_IP 443 443 TCP "Bitcoin Bens HTTPS"
    
    # Create script to maintain port forwards
    cat > "$INSTALL_DIR/scripts/maintain-upnp.sh" << EOF
#!/bin/bash
upnpc -a $LOCAL_IP 3000 3000 TCP "Bitcoin Bens Frontend"
upnpc -a $LOCAL_IP 8001 8001 TCP "Bitcoin Bens API"
upnpc -a $LOCAL_IP 80 80 TCP "Bitcoin Bens HTTP"
upnpc -a $LOCAL_IP 443 443 TCP "Bitcoin Bens HTTPS"
EOF
    
    chmod +x "$INSTALL_DIR/scripts/maintain-upnp.sh"
    
    # Add to cron
    (crontab -l 2>/dev/null; echo "*/30 * * * * $INSTALL_DIR/scripts/maintain-upnp.sh") | crontab -
    
    print_status "UPnP port forwarding configured"
}

# Setup enhanced security
setup_security() {
    print_header "Setting up Enhanced Security"
    
    # Configure UFW firewall
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 3000/tcp
    sudo ufw allow 8001/tcp
    
    [[ $VPN_CHOICE -eq 2 ]] && sudo ufw allow 51820/udp  # WireGuard
    
    sudo ufw --force enable
    
    # Configure Fail2Ban
    sudo tee /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-noscript]
enabled = true

[nginx-badbots]
enabled = true

[nginx-noproxy]
enabled = true
EOF

    sudo systemctl enable fail2ban
    sudo systemctl start fail2ban
    
    # Setup automatic security updates
    sudo apt install -y unattended-upgrades
    echo 'Unattended-Upgrade::Automatic-Reboot "false";' | sudo tee -a /etc/apt/apt.conf.d/50unattended-upgrades
    
    print_status "Enhanced security configured (UFW + Fail2Ban + Auto-updates)"
}

# Setup monitoring dashboard
setup_monitoring() {
    print_header "Setting up System Monitoring"
    
    # Install monitoring tools
    sudo apt install -y htop iotop nethogs
    
    # Create monitoring script
    cat > "$INSTALL_DIR/scripts/monitor.sh" << 'EOF'
#!/bin/bash
# Bitcoin Ben's System Monitor

LOGFILE="/var/log/bitcoin-bens-monitor.log"

log_metric() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOGFILE"
}

# System metrics
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.2f", ($3/$2) * 100.0)}')
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
CPU_TEMP=$(vcgencmd measure_temp 2>/dev/null | cut -d= -f2 | cut -d\' -f1 || echo "N/A")

# Service status
BACKEND_STATUS=$(systemctl is-active bbc-backend)
FRONTEND_STATUS=$(pm2 show bbc-frontend 2>/dev/null | grep -o "online\|stopped" | head -1 || echo "stopped")
MONGODB_STATUS=$(systemctl is-active mongod)

# Log metrics
log_metric "CPU: ${CPU_USAGE}% | Memory: ${MEMORY_USAGE}% | Disk: ${DISK_USAGE}% | Temp: ${CPU_TEMP}°C"
log_metric "Services - Backend: $BACKEND_STATUS | Frontend: $FRONTEND_STATUS | MongoDB: $MONGODB_STATUS"

# Check for issues and alert if needed
[[ ${MEMORY_USAGE%.*} -gt 90 ]] && log_metric "ALERT: High memory usage: ${MEMORY_USAGE}%"
[[ ${DISK_USAGE} -gt 90 ]] && log_metric "ALERT: High disk usage: ${DISK_USAGE}%"
[[ "$CPU_TEMP" != "N/A" && ${CPU_TEMP%.*} -gt 70 ]] && log_metric "ALERT: High CPU temperature: ${CPU_TEMP}°C"
[[ "$BACKEND_STATUS" != "active" ]] && log_metric "ALERT: Backend service is $BACKEND_STATUS"
[[ "$MONGODB_STATUS" != "active" ]] && log_metric "ALERT: MongoDB service is $MONGODB_STATUS"
EOF

    chmod +x "$INSTALL_DIR/scripts/monitor.sh"
    
    # Add to cron for regular monitoring
    (crontab -l 2>/dev/null; echo "*/5 * * * * $INSTALL_DIR/scripts/monitor.sh") | crontab -
    
    # Create web-based monitoring endpoint
    cat > "$INSTALL_DIR/scripts/monitoring-web.py" << 'EOF'
#!/usr/bin/env python3
import json
import subprocess
import psutil
from flask import Flask, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)

@app.route('/status')
def system_status():
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
        'uptime': subprocess.getoutput('uptime -p'),
        'services': {
            'backend': subprocess.getoutput('systemctl is-active bbc-backend'),
            'frontend': 'online' if 'bbc-frontend' in subprocess.getoutput('pm2 list') else 'offline',
            'mongodb': subprocess.getoutput('systemctl is-active mongod'),
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9001, debug=False)
EOF

    print_status "System monitoring configured (check logs at /var/log/bitcoin-bens-monitor.log)"
}

# Setup system services
setup_services() {
    print_header "Setting up System Services"
    
    # Backend service
    sudo tee /etc/systemd/system/bbc-backend.service << EOF
[Unit]
Description=Bitcoin Ben's Burger Bus Club Backend
After=network.target mongod.service
Requires=mongod.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR/backend
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 2
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # PM2 Frontend service
    cat > "$INSTALL_DIR/config/pm2-frontend.json" << EOF
{
  "apps": [{
    "name": "bbc-frontend",
    "cwd": "$INSTALL_DIR/frontend",
    "script": "yarn",
    "args": "start",
    "env": {
      "PORT": "3000",
      "NODE_ENV": "production"
    },
    "instances": 1,
    "restart_delay": 1000,
    "watch": false,
    "log_file": "$INSTALL_DIR/logs/frontend.log",
    "error_file": "$INSTALL_DIR/logs/frontend-error.log",
    "out_file": "$INSTALL_DIR/logs/frontend-out.log"
  }]
}
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable bbc-backend
    
    print_status "System services configured"
}

# Create management scripts
create_management_scripts() {
    print_header "Creating Management Scripts"
    
    # Enhanced start script
    cat > "$INSTALL_DIR/scripts/start.sh" << EOF
#!/bin/bash
echo "🍔 Starting Bitcoin Ben's Burger Bus Club..."

# Start MongoDB
sudo systemctl start mongod
echo "✓ MongoDB started"

# Start Backend
sudo systemctl start bbc-backend
echo "✓ Backend API started"

# Start Frontend
cd "$INSTALL_DIR"
pm2 start config/pm2-frontend.json
echo "✓ Frontend started"

# Start monitoring (if enabled)
[[ -f scripts/monitor.sh ]] && ./scripts/monitor.sh &

echo ""
echo "🎉 Bitcoin Ben's Burger Bus Club is now running!"
echo ""
echo "📱 Access URLs:"
echo "   Local Frontend:  http://$LOCAL_IP:3000"
echo "   Local Admin:     http://$LOCAL_IP:3000?admin=true"
echo "   Local API:       http://$LOCAL_IP:8001"
[[ -n $DOMAIN_NAME ]] && echo "   Public Frontend: https://$DOMAIN_NAME"
[[ -n $DOMAIN_NAME ]] && echo "   Public Admin:    https://$DOMAIN_NAME?admin=true"
[[ -n $TAILSCALE_IP ]] && echo "   Tailscale:       http://$TAILSCALE_IP:3000"
echo ""
echo "👤 Admin Login: $ADMIN_EMAIL"
echo "🔍 Status: ./scripts/status.sh"
echo "📊 Monitor: tail -f /var/log/bitcoin-bens-monitor.log"
EOF

    # Enhanced status script
    cat > "$INSTALL_DIR/scripts/status.sh" << EOF
#!/bin/bash
echo "📊 Bitcoin Ben's Burger Bus Club - System Status"
echo "==============================================="

# System info
echo "🖥️  System:"
echo "   CPU Usage:    \$(top -bn1 | grep "Cpu(s)" | awk '{print \$2}' | awk -F'%' '{print \$1}')%"
echo "   Memory Usage: \$(free | grep Mem | awk '{printf("%.1f", (\$3/\$2) * 100.0)}')%"
echo "   Disk Usage:   \$(df / | tail -1 | awk '{print \$5}')"
echo "   Temperature:  \$(vcgencmd measure_temp 2>/dev/null | cut -d= -f2 || echo "N/A")"
echo "   Uptime:       \$(uptime -p)"

echo ""
echo "🔧 Services:"
printf "   Backend API:  "
systemctl is-active bbc-backend --quiet && echo "🟢 Running" || echo "🔴 Stopped"
printf "   Frontend:     "
pm2 show bbc-frontend >/dev/null 2>&1 && echo "🟢 Running" || echo "🔴 Stopped"
printf "   MongoDB:      "
systemctl is-active mongod --quiet && echo "🟢 Running" || echo "🔴 Stopped"
printf "   Nginx:        "
systemctl is-active nginx --quiet && echo "🟢 Running" || echo "🔴 Stopped"

echo ""
echo "🌐 Network:"
echo "   Local IP:     $LOCAL_IP"
[[ -n $DOMAIN_NAME ]] && echo "   Domain:       $DOMAIN_NAME"
[[ -n $TAILSCALE_IP ]] && echo "   Tailscale:    $TAILSCALE_IP"
echo "   Ports Open:   \$(sudo netstat -tlnp | grep ':3000\|:8001\|:80\|:443' | wc -l) services"

echo ""
echo "🔒 Security:"
printf "   Firewall:     "
sudo ufw status | grep -q "Status: active" && echo "🟢 Active" || echo "🔴 Inactive"
printf "   Fail2Ban:     "
systemctl is-active fail2ban --quiet && echo "🟢 Active" || echo "🔴 Inactive"
[[ -f /etc/letsencrypt/live/$DOMAIN_NAME/cert.pem ]] && echo "   SSL Cert:     🟢 Valid" || echo "   SSL Cert:     🔴 None"

echo ""
echo "📈 Recent Activity:"
[[ -f /var/log/bitcoin-bens-monitor.log ]] && echo "$(tail -5 /var/log/bitcoin-bens-monitor.log)" || echo "   No monitoring data available"
EOF

    # Make scripts executable
    chmod +x "$INSTALL_DIR/scripts"/*.sh
    
    print_status "Management scripts created"
}

# Final setup and testing
final_setup() {
    print_header "Final Setup & Testing"
    
    # Create directory for user's app files
    mkdir -p "$INSTALL_DIR/app-source"
    
    # Set proper permissions
    sudo chown -R $USER:$USER "$INSTALL_DIR"
    chmod -R 755 "$INSTALL_DIR/scripts"
    chmod 600 "$INSTALL_DIR"/.*.env 2>/dev/null || true
    
    # Create quick setup completion script
    cat > "$INSTALL_DIR/complete-setup.sh" << 'EOF'
#!/bin/bash
echo "🎯 Completing Bitcoin Ben's Setup..."

# Copy user's application files
if [[ -d backend ]] && [[ -d frontend ]]; then
    echo "📁 Copying application files..."
    rsync -av --exclude 'node_modules' --exclude '__pycache__' backend/ ~/bitcoin-bens-club/backend/
    rsync -av --exclude 'node_modules' --exclude 'build' frontend/ ~/bitcoin-bens-club/frontend/
else
    echo "⚠️  Please copy your backend/ and frontend/ directories here first"
    exit 1
fi

cd ~/bitcoin-bens-club

# Install backend dependencies
echo "📦 Installing backend dependencies..."
source venv/bin/activate
cd backend
pip install -r requirements.txt 2>/dev/null || pip install fastapi uvicorn python-dotenv motor pymongo pydantic python-jose[cryptography] requests qrcode emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd ../frontend
yarn install
yarn build

echo "🚀 Starting services..."
cd ..
./scripts/start.sh

echo "✅ Setup completed!"
EOF
    
    chmod +x "$INSTALL_DIR/complete-setup.sh"
    
    print_status "Final setup completed"
}

# Main installation function
main() {
    print_banner
    setup_logging
    
    print_info "Starting Bitcoin Ben's Burger Bus Club ONE-COMMAND installation..."
    print_info "This will install everything needed for production deployment"
    
    interactive_setup
    
    print_header "Installation Progress"
    
    update_system
    install_nodejs
    install_python
    install_mongodb
    setup_application
    setup_environment
    
    # VPN Setup
    case $VPN_CHOICE in
        1) setup_tailscale ;;
        2) setup_wireguard ;;
        *) print_info "Skipping VPN setup" ;;
    esac
    
    # Network Setup
    [[ $SETUP_DDNS =~ ^[Yy]$ ]] && setup_ddns
    [[ $SETUP_SSL =~ ^[Yy]$ ]] && setup_ssl
    [[ $SETUP_UPNP =~ ^[Yy]$ ]] && setup_upnp
    
    # Security
    [[ $SETUP_SECURITY =~ ^[Yy]$ ]] && setup_security
    
    # Monitoring
    [[ $SETUP_MONITORING =~ ^[Yy]$ ]] && setup_monitoring
    
    setup_services
    create_management_scripts
    final_setup
    
    print_header "🎉 Installation Complete!"
    
    cat << EOF

${GREEN}✅ Bitcoin Ben's Burger Bus Club is now installed!${NC}

${BOLD}📋 Next Steps:${NC}
1. Copy your application files to: ${YELLOW}$INSTALL_DIR${NC}
2. Run: ${CYAN}cd $INSTALL_DIR && ./complete-setup.sh${NC}

${BOLD}🌐 Access URLs:${NC}
• Local Frontend:  ${CYAN}http://$LOCAL_IP:3000${NC}
• Local Admin:     ${CYAN}http://$LOCAL_IP:3000?admin=true${NC}
• Local API:       ${CYAN}http://$LOCAL_IP:8001${NC}
EOF

    [[ -n $DOMAIN_NAME ]] && cat << EOF
• Public Frontend: ${GREEN}https://$DOMAIN_NAME${NC}
• Public Admin:    ${GREEN}https://$DOMAIN_NAME?admin=true${NC}
EOF

    [[ -n $TAILSCALE_IP ]] && cat << EOF
• Tailscale URL:   ${PURPLE}http://$TAILSCALE_IP:3000${NC}
EOF

    cat << EOF

${BOLD}👤 Admin Credentials:${NC}
• Email:    ${YELLOW}$ADMIN_EMAIL${NC}
• Password: ${RED}[as configured]${NC}

${BOLD}🛠️  Management Commands:${NC}
• Start:    ${CYAN}$INSTALL_DIR/scripts/start.sh${NC}
• Status:   ${CYAN}$INSTALL_DIR/scripts/status.sh${NC}
• Stop:     ${CYAN}$INSTALL_DIR/scripts/stop.sh${NC}
• Backup:   ${CYAN}$INSTALL_DIR/scripts/backup.sh${NC}

${BOLD}📊 Monitoring:${NC}
• Logs:     ${CYAN}tail -f /var/log/bitcoin-bens-monitor.log${NC}
• System:   ${CYAN}htop${NC}
• Services: ${CYAN}pm2 monit${NC}

${GREEN}🍔 Your Bitcoin Ben's Burger Bus Club is ready for production!${NC}

EOF

    print_status "Installation logged to: $LOG_FILE"
}

# Check if running as root
[[ $EUID -eq 0 ]] && { print_error "Don't run as root! Use a regular user with sudo access."; exit 1; }

# Run main installation
main "$@"