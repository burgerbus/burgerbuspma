#!/bin/bash

# Bitcoin Ben's API Server - Pi5 Installation Script

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'
BOLD='\033[1m'

print_banner() {
    echo -e "${YELLOW}${BOLD}"
    cat << 'BANNER'
    ╔══════════════════════════════════════════════════════════════╗
    ║  🍔 Bitcoin Ben's Burger Bus Club - API Server Setup 🍔    ║
    ║                                                              ║
    ║           🚀 Backend API Server for Pi5 🚀                 ║
    ║                                                              ║
    ║  Production Ready • SSL Support • Admin Panel • Monitoring  ║
    ╚══════════════════════════════════════════════════════════════╝
BANNER
    echo -e "${NC}"
}

print_status() { echo -e "${GREEN}[✓]${NC} $1"; }
print_info() { echo -e "${BLUE}[ℹ]${NC} $1"; }
print_error() { echo -e "${RED}[✗]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; }

INSTALL_DIR="$HOME/bitcoin-bens-api"
LOCAL_IP=$(hostname -I | awk '{print $1}')

# Interactive configuration
configure_setup() {
    print_info "Bitcoin Ben's API Server Configuration"
    echo ""
    
    # Admin credentials  
    read -p "Admin email [admin@bitcoinben.local]: " ADMIN_EMAIL
    ADMIN_EMAIL=${ADMIN_EMAIL:-admin@bitcoinben.local}
    
    while true; do
        read -s -p "Admin password (min 8 chars): " ADMIN_PASSWORD
        echo
        if [[ ${#ADMIN_PASSWORD} -ge 8 ]]; then
            break
        else
            print_error "Password must be at least 8 characters."
        fi
    done
    
    # Network configuration
    read -p "Enable internet access with SSL? (y/n): " SETUP_SSL
    read -p "Setup VPN access (Tailscale)? (y/n): " SETUP_VPN
    
    echo ""
    print_info "Configuration Summary:"
    print_info "• API will be available at: http://$LOCAL_IP:8001"
    print_info "• API Documentation: http://$LOCAL_IP:8001/docs"  
    print_info "• Admin: $ADMIN_EMAIL"
    [[ $SETUP_SSL =~ ^[Yy]$ ]] && print_info "• SSL: Yes"
    [[ $SETUP_VPN =~ ^[Yy]$ ]] && print_info "• VPN: Yes"
    echo ""
}

# Update system
update_system() {
    print_info "Updating system packages..."
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y curl wget git build-essential python3 python3-pip python3-venv
    print_status "System updated"
}

# Install MongoDB
install_mongodb() {
    print_info "Installing MongoDB 7.0..."
    
    curl -fsSL https://pgp.mongodb.com/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    
    sudo apt update && sudo apt install -y mongodb-org
    sudo systemctl enable mongod && sudo systemctl start mongod
    
    print_status "MongoDB installed and running"
}

# Setup API server
setup_api_server() {
    print_info "Setting up API server..."
    
    mkdir -p "$INSTALL_DIR"/{logs,backups,scripts}
    
    # Copy API source
    cp -r ../api-source/backend/* "$INSTALL_DIR/"
    
    # Create Python virtual environment
    cd "$INSTALL_DIR"
    python3 -m venv venv
    source venv/bin/activate
    
    # Install Python dependencies
    pip install --upgrade pip
    pip install fastapi uvicorn python-dotenv motor pymongo pydantic
    pip install python-jose[cryptography] requests qrcode bcrypt
    pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
    
    # Create requirements.txt
    pip freeze > requirements.txt
    
    print_status "API server setup complete"
}

# Configure environment
configure_environment() {
    print_info "Configuring environment..."
    
    JWT_SECRET=$(openssl rand -hex 64)
    
    cat > "$INSTALL_DIR/.env" << EOF
# Database Configuration
MONGO_URL="mongodb://localhost:27017/bitcoin_bens_club"
DB_NAME="bitcoin_bens_club"

# Server Configuration
HOST=0.0.0.0
PORT=8001

# CORS Origins (update with your app domains)
CORS_ORIGINS=["*"]

# Security
JWT_SECRET_KEY="$JWT_SECRET"
ADMIN_EMAIL="$ADMIN_EMAIL"
ADMIN_PASSWORD="$ADMIN_PASSWORD"

# BCH Configuration  
BCH_RECEIVING_ADDRESS="bitcoincash:qph0duvh0zn0r2um7znh8gx20p50dr3ycc5lcp0sc4"

# Pump.fun Token
PUMP_FUN_TOKEN_ADDRESS="mWusXdRfsYAoFtYdaDcf8tmG7hnRNvnVc2TuvNEpump"

# API Configuration
API_TITLE="Bitcoin Ben's Burger Bus Club API"
API_DESCRIPTION="Backend API for Bitcoin Ben's membership and ordering system"
API_VERSION="1.0.0"
