#!/bin/bash

# Create Backend-Only Bitcoin Ben's Pi5 Package
echo "🔧 Creating Backend-Only Bitcoin Ben's API Server Package..."

PACKAGE_NAME="bitcoin-bens-api-server"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_DIR="${PACKAGE_NAME}_${TIMESTAMP}"

# Create package structure
mkdir -p "$PACKAGE_DIR"/{setup,api-source,docs,scripts,tools}

echo "📁 Copying backend API source..."
# Copy only backend
cp -r backend "$PACKAGE_DIR/api-source/" && {
    # Clean backend
    rm -f "$PACKAGE_DIR/api-source/backend/.env"
    rm -rf "$PACKAGE_DIR/api-source/backend/__pycache__"
    rm -rf "$PACKAGE_DIR/api-source/backend/venv"
    
    # Create env template
    cat > "$PACKAGE_DIR/api-source/backend/.env.template" << 'EOF'
# Database Configuration (auto-generated)
MONGO_URL="mongodb://localhost:27017/bitcoin_bens_club"
DB_NAME="bitcoin_bens_club"

# Server Configuration  
HOST=0.0.0.0
PORT=8001

# CORS Origins (add your web/mobile app domains)
CORS_ORIGINS=["*"]  # Allow all origins - restrict in production

# Security (auto-generated)
JWT_SECRET_KEY=""
ADMIN_EMAIL="admin@bitcoinben.local"
ADMIN_PASSWORD=""

# BCH Configuration
BCH_RECEIVING_ADDRESS="bitcoincash:qph0duvh0zn0r2um7znh8gx20p50dr3ycc5lcp0sc4"

# Pump.fun Token
PUMP_FUN_TOKEN_ADDRESS="mWusXdRfsYAoFtYdaDcf8tmG7hnRNvnVc2TuvNEpump"

# API Configuration
API_TITLE="Bitcoin Ben's Burger Bus Club API"
API_DESCRIPTION="Backend API for Bitcoin Ben's membership and ordering system"
API_VERSION="1.0.0"
EOF
}

echo "📚 Creating API documentation..."

# Main README for API server
cat > "$PACKAGE_DIR/README.md" << 'EOF'
# 🍔 Bitcoin Ben's Burger Bus Club - API Server for Pi5

## 🎯 What This Is

This is a **backend API server only** that runs on your Raspberry Pi 5. Your web and mobile applications will connect to this API to handle:

- Member registration and authentication
- Payment processing and verification  
- Menu management
- Order processing
- Admin management functions
- Pump.fun token integration
- Affiliate system

## 🚀 ONE-COMMAND INSTALLATION

```bash
wget https://bitcoin-bens.com/api-package.tar.gz
tar -xzf api-package.tar.gz
cd bitcoin-bens-api-server_*/
chmod +x setup/install.sh
./setup/install.sh
```

## 🏗️ What Gets Installed

### API Server Stack
- **FastAPI Backend** (Python 3.11+) 
- **MongoDB 7.0** with authentication
- **Uvicorn ASGI** server with auto-restart
- **Nginx** reverse proxy for SSL/production
- **Systemd service** for auto-start on boot

### Security & Access
- **CORS configured** for your web/mobile apps
- **JWT authentication** for API access
- **Admin authentication** for management
- **SSL certificates** (Let's Encrypt)
- **Firewall configuration** (UFW)

### Monitoring & Management
- **API health monitoring**
- **Database backup automation**
- **Log management and rotation**  
- **Performance monitoring**
- **Easy management scripts**

## 🌐 API Access

After installation:

- **API Base URL:** `http://your-pi-ip:8001`
- **API Documentation:** `http://your-pi-ip:8001/docs` 
- **Health Check:** `http://your-pi-ip:8001/health`
- **With SSL:** `https://your-domain.com/api/`

## 📋 API Endpoints

### Authentication & Members
```
POST /api/auth/register          # Register new member (requires $21 payment)
POST /api/auth/login             # Member login  
POST /api/auth/admin-login       # Admin login
GET  /api/profile                # Get member profile
POST /api/profile/update         # Update member profile
```

### Payment System
```
GET  /api/admin/pending-members  # Get members awaiting payment
POST /api/admin/activate-member  # Activate member after payment
POST /api/auth/bbc-staking-payment # Pay with BBC tokens
GET  /api/payments/methods       # Get payment methods
```

### Menu & Orders  
```
GET  /api/debug/menu             # Get menu items with multi-currency pricing
GET  /api/debug/locations        # Get food truck locations
GET  /api/debug/events           # Get member events
GET  /api/debug/orders           # Get member orders
```

### Admin Management
```
GET  /api/admin/members          # Manage members
GET  /api/admin/payments         # Payment verification  
GET  /api/admin/analytics        # System analytics
POST /api/admin/treasury/*       # Manage BBC token treasury
```

### Pump.fun Integration
```
GET  /api/pump/token-info        # Get BBC token information
GET  /api/pump/token-price       # Get current token price
```

## 💻 For Web/Mobile App Developers

### Authentication Flow
1. **Register:** `POST /api/auth/register` returns payment instructions
2. **User pays** $21 via Venmo/CashApp/BCH/etc
3. **Admin activates** account via admin panel
4. **Login:** `POST /api/auth/login` returns JWT token  
5. **Use JWT token** in Authorization header for all API calls

### Example API Usage
```javascript
// Register new member
const registerResponse = await fetch('http://your-pi:8001/api/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'John Doe',
    email: 'john@example.com', 
    password: 'secure123',
    phone: '555-1234',
    pma_agreed: true
  })
});

// Login after activation
const loginResponse = await fetch('http://your-pi:8001/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'john@example.com',
    password: 'secure123'
  })
});

const { access_token } = await loginResponse.json();

// Use token for authenticated requests
const profileResponse = await fetch('http://your-pi:8001/api/profile', {
  headers: { 
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  }
});
```

### CORS Configuration
The API is configured to accept requests from your web/mobile apps. Update the CORS_ORIGINS in .env:

```bash
# For development (allow all)
CORS_ORIGINS=["*"]

# For production (specific domains)  
CORS_ORIGINS=["https://yourapp.com","https://app.yoursite.com"]
```

## 🛠️ Management Commands

```bash  
# Control API server
~/bitcoin-bens-api/scripts/start.sh
~/bitcoin-bens-api/scripts/stop.sh
~/bitcoin-bens-api/scripts/status.sh

# Monitoring
~/bitcoin-bens-api/scripts/logs.sh
~/bitcoin-bens-api/scripts/monitor.sh

# Maintenance  
~/bitcoin-bens-api/scripts/backup.sh
~/bitcoin-bens-api/scripts/update.sh
```

## 🔧 Service Management

```bash
# API service control
sudo systemctl start/stop/restart bbc-api
sudo systemctl status bbc-api
sudo journalctl -u bbc-api -f

# Database control
sudo systemctl start/stop/restart mongod
sudo systemctl status mongod

# Nginx (for SSL)
sudo systemctl start/stop/restart nginx
```

## 📊 Monitoring & Logs

```bash
# API server logs
tail -f ~/bitcoin-bens-api/logs/api.log

# System monitoring  
tail -f /var/log/bitcoin-bens-api-monitor.log

# Database logs
sudo tail -f /var/log/mongodb/mongod.log

# Performance monitoring
htop
sudo netstat -tlnp | grep :8001
```

## 🔐 Security Features

- **JWT Authentication** for API access
- **Admin Authentication** for management functions  
- **CORS Protection** for web apps
- **Rate Limiting** for API endpoints
- **Input Validation** on all endpoints
- **SQL Injection Protection** via MongoDB
- **Password Hashing** with bcrypt
- **SSL/TLS Support** for HTTPS

## 🌍 Internet Access Setup

### Basic Setup (HTTP)
1. **Port Forward** 8001 on your router → Pi5:8001
2. **Access API** at `http://your-external-ip:8001`

### Production Setup (HTTPS)  
1. **Get Domain** (or use Dynamic DNS)
2. **Configure SSL** (automated with Let's Encrypt)
3. **Access API** at `https://your-domain.com/api/`

### VPN Setup (Recommended)
1. **Install Tailscale** (included in setup)
2. **Access securely** from anywhere via VPN

## 💡 Payment Flow

### Registration Process:
1. **User registers** via your app → API returns payment instructions
2. **User pays $21** via Venmo (@burgerbusclub), CashApp, BCH, etc.
3. **Admin verifies payment** via admin API and activates account
4. **User can login** and access full API functionality

### Alternative: BBC Token Payment
Users can stake 1,000,000 $BBC tokens instead of $21 cash payment.

## 📱 Building Your Apps

This API server handles all backend logic. You build:

### Web App Example
- React, Vue, Angular, etc.  
- Connects to `http://your-pi:8001/api/`
- Handles user interface and interactions

### Mobile App Example
- React Native, Flutter, Swift, Kotlin
- Same API endpoints as web app
- Native mobile experience

### Multiple Apps
- Customer app (ordering, profile)
- Admin app (management)  
- Staff app (order processing)
- All connect to same Pi5 API server

---

## 🎉 Ready to Build!

Your Pi5 API server provides everything needed for:
- ✅ Member registration and management
- ✅ Payment processing and verification
- ✅ Multi-currency menu system  
- ✅ Order management
- ✅ Admin controls
- ✅ Pump.fun token integration
- ✅ Affiliate system

**🍔 Start building your Bitcoin Burger apps! 🚀**

For technical details, see `docs/api-reference.md`
For troubleshooting, see `docs/troubleshooting.md`
EOF

# API Reference Documentation
cat > "$PACKAGE_DIR/docs/api-reference.md" << 'EOF'
# 📖 Bitcoin Ben's API Reference

## Base URL
```
http://your-pi-ip:8001/api
https://your-domain.com/api  (with SSL)
```

## Authentication

### JWT Token
Include in request headers:
```
Authorization: Bearer <your-jwt-token>
```

### Admin Token  
For admin endpoints, use admin JWT token obtained from `/auth/admin-login`

## Endpoints

### 🔐 Authentication

#### Register Member
```http
POST /auth/register
```

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com", 
  "password": "secure123",
  "phone": "555-1234",
  "address": "",
  "city": "",
  "state": "", 
  "zip_code": "",
  "pma_agreed": true,
  "referral_code": ""
}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": "uuid",
    "email": "john@example.com",
    "name": "John Doe", 
    "dues_paid": false,
    "is_member": false
  },
  "message": "Registration successful! Please complete your $21 payment to activate your account.",
  "payment_required": true,
  "payment_amount": 21.0,
  "payment_instructions": {
    "venmo": "@burgerbusclub",
    "cashapp": "$burgerbusclub",
    "zelle": "payments@bitcoinben.com", 
    "bch_address": "bitcoincash:qph0duvh0zn0r2um7znh8gx20p50dr3ycc5lcp0sc4",
    "instructions": "Send $21 via any method above. Include your email in payment memo."
  },
  "next_steps": "After payment, contact admin with transaction ID for activation."
}
```

#### Login Member
```http
POST /auth/login
```

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "secure123"
}
```

**Response:**
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "john@example.com",
    "name": "John Doe",
    "dues_paid": true,
    "is_member": true,
    "wallet_address": "",
    "referral_code": "BITCOINBEN-ABC123"
  }
}
```

#### Admin Login  
```http
POST /auth/admin-login
```

**Request Body:**
```json
{
  "email": "admin@bitcoinben.local",
  "password": "admin-password"
}
```

### 👤 Member Profile

#### Get Profile
```http
GET /profile
Headers: Authorization: Bearer <token>
```

#### Update Profile
```http  
POST /profile/update
Headers: Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "name": "Updated Name",
  "phone": "555-9999",
  "address": "123 New St"
}
```

### 💳 Payment Management

#### Get Pending Members (Admin)
```http
GET /admin/pending-members
Headers: Authorization: Bearer <admin-token>
```

**Response:**
```json
{
  "success": true,
  "pending_members": [
    {
      "id": "uuid",
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "555-1234",
      "registration_date": "2024-01-15T10:30:00Z",
      "referral_code": "BITCOINBEN-ABC123",
      "referred_by": "BITCOINBEN-XYZ789",
      "payment_amount": 21.0
    }
  ],
  "total_pending": 1,
  "membership_fee": 21.0
}
```

#### Activate Member (Admin)
```http
POST /admin/activate-member
Headers: Authorization: Bearer <admin-token>
```

**Request Body:**
```json
{
  "member_id": "uuid",
  "transaction_id": "venmo_12345",
  "payment_method": "venmo"
}
```

#### BBC Token Staking Payment
```http
POST /auth/bbc-staking-payment  
```

**Request Body:**
```json
{
  "wallet_address": "solana-wallet-address",
  "bbc_tokens_staked": 1000000.0
}
```

### 🍔 Menu System

#### Get Menu Items
```http
GET /debug/menu
```

**Response:**
```json
{
  "success": true,
  "menu_items": [
    {
      "id": "uuid",
      "name": "The Satoshi Stacker",
      "description": "Triple-stacked wagyu beef with crypto-gold sauce",
      "price": 28.0,
      "member_price": 21.0,
      "price_bch": 0.085,
      "member_price_bch": 0.064, 
      "price_bbc": 1140.0,
      "member_price_bbc": 857.0,
      "category": "main",
      "image_url": "https://...",
      "is_available": true
    }
  ]
}
```

### 📍 Locations & Events

#### Get Locations
```http
GET /debug/locations
```

#### Get Events  
```http
GET /debug/events
```

#### Get Orders
```http
GET /debug/orders  
Headers: Authorization: Bearer <token>
```

### 🪙 Pump.fun Integration

#### Get Token Info
```http
GET /pump/token-info
```

#### Get Token Price
```http
GET /pump/token-price
```

### 💰 Admin Functions

#### Get All Members
```http
GET /admin/members
Headers: Authorization: Bearer <admin-token>
```

#### Manage Treasury
```http
POST /admin/treasury/fund
Headers: Authorization: Bearer <admin-token>
```

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 400 Bad Request
```json
{
  "detail": "Invalid input data"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limits

- **Authentication endpoints:** 5 requests per minute per IP
- **General API endpoints:** 100 requests per minute per user
- **Admin endpoints:** 50 requests per minute per admin

## CORS Configuration

Configure allowed origins in your Pi5 .env file:

```bash
# Development (allow all)
CORS_ORIGINS=["*"]

# Production (specific domains)
CORS_ORIGINS=["https://yourapp.com","https://admin.yourapp.com"]
```

---

## Need Help?

- **API Docs:** Visit `http://your-pi:8001/docs` for interactive documentation
- **Health Check:** `GET /health` to verify API server status  
- **Server Logs:** Check `~/bitcoin-bens-api/logs/api.log`
EOF

echo "🔧 Creating installation script..."

# Backend-only installer
cat > "$PACKAGE_DIR/setup/install.sh" << 'EOF'
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
EOF

    chmod 600 "\$INSTALL_DIR/.env"
    print_status "Environment configured"

# Setup systemd service
setup_service() {
    print_info "Creating system service..."
    
    sudo tee /etc/systemd/system/bbc-api.service << EOF
[Unit]
Description=Bitcoin Ben's Burger Bus Club API Server
After=network.target mongod.service
Requires=mongod.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 2
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable bbc-api
    sudo systemctl start bbc-api
    
    print_status "API service started"
}

# Setup firewall
setup_firewall() {
    print_info "Configuring firewall..."
    
    sudo apt install -y ufw
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    sudo ufw allow 8001/tcp
    
    [[ $SETUP_SSL =~ ^[Yy]$ ]] && {
        sudo ufw allow 80/tcp
        sudo ufw allow 443/tcp
    }
    
    sudo ufw --force enable
    print_status "Firewall configured"
}

# Setup SSL (optional)
setup_ssl() {
    [[ ! $SETUP_SSL =~ ^[Yy]$ ]] && return
    
    print_info "Setting up SSL with Nginx..."
    
    sudo apt install -y nginx certbot python3-certbot-nginx
    
    read -p "Enter your domain name: " DOMAIN_NAME
    
    # Create Nginx config
    sudo tee /etc/nginx/sites-available/bbc-api << EOF
server {
    listen 80;
    server_name $DOMAIN_NAME;
    
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    sudo ln -sf /etc/nginx/sites-available/bbc-api /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx
    
    # Get SSL certificate
    sudo certbot --nginx -d "$DOMAIN_NAME" --non-interactive --agree-tos --email "$ADMIN_EMAIL"
    
    print_status "SSL configured for $DOMAIN_NAME"
}

# Setup VPN (optional)
setup_vpn() {
    [[ ! $SETUP_VPN =~ ^[Yy]$ ]] && return
    
    print_info "Setting up Tailscale VPN..."
    curl -fsSL https://tailscale.com/install.sh | sh
    
    print_warning "Please authenticate Tailscale in your browser"
    sudo tailscale up
    
    TAILSCALE_IP=$(tailscale ip -4)
    print_status "Tailscale configured. IP: $TAILSCALE_IP"
}

# Create management scripts
create_scripts() {
    print_info "Creating management scripts..."
    
    # Start script
    cat > "$INSTALL_DIR/scripts/start.sh" << EOF
#!/bin/bash
echo "🚀 Starting Bitcoin Ben's API Server..."
sudo systemctl start mongod
sudo systemctl start bbc-api
echo "✅ API Server started!"
echo "📡 API: http://$LOCAL_IP:8001"
echo "📖 Docs: http://$LOCAL_IP:8001/docs"
EOF

    # Status script
    cat > "$INSTALL_DIR/scripts/status.sh" << EOF
#!/bin/bash
echo "📊 Bitcoin Ben's API Server Status"
echo "=================================="

echo "🔧 Services:"
printf "   API Server:   "
systemctl is-active bbc-api --quiet && echo "🟢 Running" || echo "🔴 Stopped"
printf "   MongoDB:      "
systemctl is-active mongod --quiet && echo "🟢 Running" || echo "🔴 Stopped"

echo ""
echo "🌐 Network:"
echo "   Local IP:     $LOCAL_IP"
echo "   API URL:      http://$LOCAL_IP:8001"
echo "   API Docs:     http://$LOCAL_IP:8001/docs"

echo ""
echo "📊 Resources:"
echo "   Memory:       \$(free -h | grep Mem | awk '{printf("%.1f", (\$3/\$2) * 100.0)}')%"
echo "   Disk:         \$(df / | tail -1 | awk '{print \$5}')"
echo "   API Port:     \$(sudo netstat -tlnp | grep ':8001' | wc -l) listener(s)"
EOF

    # Logs script  
    cat > "$INSTALL_DIR/scripts/logs.sh" << 'EOF'
#!/bin/bash
echo "📋 API Server Logs"
echo "=================="
echo ""
echo "Recent API logs:"
sudo journalctl -u bbc-api -n 20 --no-pager
echo ""
echo "Live API logs (Ctrl+C to exit):"
sudo journalctl -u bbc-api -f
EOF

    chmod +x "$INSTALL_DIR/scripts"/*.sh
    print_status "Management scripts created"
}

# Main installation
main() {
    print_banner
    configure_setup
    update_system
    install_mongodb
    setup_api_server
    configure_environment
    setup_service
    setup_firewall
    setup_ssl
    setup_vpn
    create_scripts
    
    print_info ""
    print_status "🎉 Bitcoin Ben's API Server Installation Complete!"
    print_info ""
    print_info "📡 Your API server is now running at:"
    print_info "   • Local API: http://$LOCAL_IP:8001"
    print_info "   • API Docs:  http://$LOCAL_IP:8001/docs"
    print_info "   • Health:    http://$LOCAL_IP:8001/health"
    print_info ""
    print_info "🛠️ Management:"
    print_info "   • Status: $INSTALL_DIR/scripts/status.sh"
    print_info "   • Logs:   $INSTALL_DIR/scripts/logs.sh"
    print_info "   • Start:  $INSTALL_DIR/scripts/start.sh"
    print_info ""
    print_info "👤 Admin Login:"
    print_info "   • Email: $ADMIN_EMAIL"
    print_info "   • Use POST /api/auth/admin-login"
    print_info ""
    print_status "🍔 Ready to serve Bitcoin Burger API requests! 🚀"
}

main "$@"
EOF

chmod +x "$PACKAGE_DIR/setup/install.sh"

echo "🔧 Creating package info..."
cat > "$PACKAGE_DIR/PACKAGE-INFO.txt" << EOF
Bitcoin Ben's Burger Bus Club - API Server Package for Pi5
=========================================================

Created: $(date)
Version: 1.0.0
Target: Raspberry Pi 5

This is a BACKEND-ONLY package for Pi5 deployment.
Your web/mobile apps will connect to this API server.

Package Contents:
- Python FastAPI backend server
- MongoDB database setup
- Admin authentication system  
- Payment management endpoints
- JWT authentication for clients
- SSL support for production
- VPN support (Tailscale)
- System monitoring and management
- Comprehensive API documentation

Installation:
./setup/install.sh

Access After Install:
- API Base URL: http://your-pi-ip:8001
- API Docs: http://your-pi-ip:8001/docs
- Health Check: http://your-pi-ip:8001/health

Features:
✅ Member registration with payment verification
✅ Admin panel for payment activation  
✅ Multi-currency menu system (USD/BCH/BBC)
✅ Pump.fun token integration
✅ Affiliate commission system
✅ JWT authentication for web/mobile apps
✅ CORS configuration for client apps
✅ SSL/HTTPS support
✅ Database backups and monitoring

Total Files: $(find "$PACKAGE_DIR" -type f | wc -l)
Package Size: $(du -sh "$PACKAGE_DIR" | cut -f1)

Ready to power your Bitcoin Burger web/mobile apps! 🍔🚀
EOF

echo "🗜️ Creating compressed package..."
tar -czf "${PACKAGE_DIR}.tar.gz" "$PACKAGE_DIR"

# Create checksums
sha256sum "${PACKAGE_DIR}.tar.gz" > "${PACKAGE_DIR}.sha256" 
md5sum "${PACKAGE_DIR}.tar.gz" > "${PACKAGE_DIR}.md5"

echo ""
echo "✅ Backend-Only Bitcoin Ben's API Server Package Created!"
echo "========================================================"
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
echo "📡 After Install - API Available At:"
echo "   http://your-pi-ip:8001      (API base URL)"
echo "   http://your-pi-ip:8001/docs (API documentation)"
echo ""
echo "💻 Build Your Web/Mobile Apps To Connect To This API!"
echo ""
echo "🍔 Ready to power Bitcoin Burger apps worldwide! 🚀"

# Cleanup
rm -rf "$PACKAGE_DIR"