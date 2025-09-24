#!/bin/bash

# Bitcoin Ben's Burger Bus Club - Raspberry Pi 5 Setup Script
# This script sets up the complete application on Pi5 with local MongoDB

set -e  # Exit on any error

echo "🍔 Bitcoin Ben's Burger Bus Club - Pi5 Setup Starting..."
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

# Check if running on Pi5
check_pi5() {
    print_header "Checking Raspberry Pi 5"
    
    if ! grep -q "Raspberry Pi 5" /proc/cpuinfo 2>/dev/null; then
        print_warning "This script is optimized for Raspberry Pi 5, but will continue..."
    else
        print_status "Raspberry Pi 5 detected ✓"
    fi
    
    # Check available memory
    MEMORY_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    MEMORY_GB=$((MEMORY_KB / 1024 / 1024))
    
    if [ $MEMORY_GB -lt 4 ]; then
        print_warning "Recommended: 4GB+ RAM. Current: ${MEMORY_GB}GB"
        print_warning "Performance may be limited with less than 4GB RAM"
    else
        print_status "Memory: ${MEMORY_GB}GB ✓"
    fi
}

# Update system
update_system() {
    print_header "Updating System Packages"
    
    sudo apt update
    sudo apt upgrade -y
    sudo apt install -y curl wget git htop unzip build-essential
    
    print_status "System updated ✓"
}

# Install Node.js
install_nodejs() {
    print_header "Installing Node.js 18.x LTS"
    
    if command -v node >/dev/null 2>&1; then
        NODE_VERSION=$(node -v)
        print_status "Node.js already installed: $NODE_VERSION"
    else
        # Install Node.js 18.x LTS
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
        
        # Install Yarn
        curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
        echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
        sudo apt update
        sudo apt install -y yarn
        
        print_status "Node.js and Yarn installed ✓"
    fi
    
    # Install PM2 globally for process management
    sudo npm install -g pm2
    print_status "PM2 process manager installed ✓"
}

# Install Python 3.11+
install_python() {
    print_header "Setting up Python Environment"
    
    # Install Python 3.11+ and pip
    sudo apt install -y python3 python3-pip python3-venv python3-dev
    
    # Create virtual environment for the application
    python3 -m venv ~/bitcoin-bens-club/venv
    source ~/bitcoin-bens-club/venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    print_status "Python environment ready ✓"
}

# Install MongoDB locally
install_mongodb() {
    print_header "Installing MongoDB 7.0 Community Edition"
    
    # Import MongoDB GPG key
    curl -fsSL https://pgp.mongodb.com/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
    
    # Add MongoDB repository
    echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    
    # Update package list
    sudo apt update
    
    # Install MongoDB
    sudo apt install -y mongodb-org
    
    # Start and enable MongoDB
    sudo systemctl start mongod
    sudo systemctl enable mongod
    
    print_status "MongoDB installed and started ✓"
    
    # Create admin user
    print_status "Setting up MongoDB authentication..."
    
    # Wait for MongoDB to fully start
    sleep 5
    
    # Create admin user
    mongosh --eval "
        use admin;
        db.createUser({
            user: 'bbcadmin',
            pwd: 'bbc-secure-$(date +%s)',
            roles: ['root']
        });
    "
    
    # Enable authentication
    sudo sed -i 's/#security:/security:\n  authorization: enabled/' /etc/mongod.conf
    sudo systemctl restart mongod
    
    print_status "MongoDB authentication configured ✓"
}

# Setup application directories
setup_directories() {
    print_header "Setting up Application Directories"
    
    cd ~/bitcoin-bens-club
    
    # Create directory structure
    mkdir -p backend frontend config logs backups scripts ssl
    
    print_status "Directory structure created ✓"
}

# Install application dependencies
install_app_dependencies() {
    print_header "Installing Application Dependencies"
    
    cd ~/bitcoin-bens-club
    
    # Activate Python virtual environment
    source venv/bin/activate
    
    # Install Python dependencies for backend
    cd backend
    pip install fastapi uvicorn python-dotenv motor pymongo pydantic
    pip install python-jose[cryptography] python-multipart requests qrcode
    pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
    
    # Create requirements.txt
    pip freeze > requirements.txt
    
    print_status "Backend dependencies installed ✓"
    
    # Install Frontend dependencies
    cd ../frontend
    
    # Check if package.json exists, if not create basic React app
    if [ ! -f package.json ]; then
        npx create-react-app . --template typescript
    fi
    
    # Install additional dependencies
    yarn add axios @solana/wallet-adapter-base @solana/wallet-adapter-react
    yarn add @solana/wallet-adapter-wallets @solana/web3.js
    yarn add qrcode.react tailwindcss postcss autoprefixer
    
    print_status "Frontend dependencies installed ✓"
}

# Configure environment variables
configure_environment() {
    print_header "Configuring Environment Variables"
    
    # Get Pi's local IP
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    
    # Admin credentials setup
    echo ""
    read -p "Enter admin email (default: admin@bitcoinben.local): " ADMIN_EMAIL
    ADMIN_EMAIL=${ADMIN_EMAIL:-admin@bitcoinben.local}
    
    read -s -p "Enter admin password (default: bbcpi5admin): " ADMIN_PASSWORD
    ADMIN_PASSWORD=${ADMIN_PASSWORD:-bbcpi5admin}
    echo ""
    
    # Backend environment
    cat > ~/bitcoin-bens-club/backend/.env << EOF
# MongoDB Configuration
MONGO_URL="mongodb://bbcadmin:bbc-secure-$(date +%s)@localhost:27017/bitcoin_bens_club?authSource=admin"
DB_NAME="bitcoin_bens_club"

# Server Configuration
HOST=0.0.0.0
PORT=8001
CORS_ORIGINS=["http://localhost:3000","http://${LOCAL_IP}:3000","http://bitcoinben.local:3000"]

# Authentication
JWT_SECRET_KEY="bbc-pi5-$(openssl rand -hex 32)"
ADMIN_EMAIL="${ADMIN_EMAIL}"
ADMIN_PASSWORD="${ADMIN_PASSWORD}"

# BCH Configuration
BCH_RECEIVING_ADDRESS="bitcoincash:qph0duvh0zn0r2um7znh8gx20p50dr3ycc5lcp0sc4"

# Pump.fun Token Configuration
PUMP_FUN_TOKEN_ADDRESS="mWusXdRfsYAoFtYdaDcf8tmG7hnRNvnVc2TuvNEpump"

# Emergent LLM Key (optional)
EMERGENT_LLM_KEY=""
EOF

    # Frontend environment
    cat > ~/bitcoin-bens-club/frontend/.env << EOF
REACT_APP_BACKEND_URL=http://${LOCAL_IP}:8001
GENERATE_SOURCEMAP=false
EOF

    print_status "Environment variables configured ✓"
    print_status "Admin credentials: ${ADMIN_EMAIL} / ${ADMIN_PASSWORD}"
}

# Setup systemd services
setup_services() {
    print_header "Setting up System Services"
    
    # Backend service
    sudo tee /etc/systemd/system/bbc-backend.service > /dev/null << EOF
[Unit]
Description=Bitcoin Ben's Burger Bus Club Backend
After=network.target mongod.service
Requires=mongod.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/bitcoin-bens-club/backend
Environment=PATH=/home/pi/bitcoin-bens-club/venv/bin
ExecStart=/home/pi/bitcoin-bens-club/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Frontend service (using PM2)
    cat > ~/bitcoin-bens-club/config/pm2-frontend.json << EOF
{
  "apps": [{
    "name": "bbc-frontend",
    "cwd": "/home/pi/bitcoin-bens-club/frontend",
    "script": "yarn",
    "args": "start",
    "env": {
      "PORT": "3000"
    },
    "restart_delay": 1000,
    "watch": false
  }]
}
EOF

    # Enable and start backend service
    sudo systemctl daemon-reload
    sudo systemctl enable bbc-backend
    
    print_status "System services configured ✓"
}

# Setup firewall
setup_firewall() {
    print_header "Configuring Firewall"
    
    # Install and configure UFW
    sudo apt install -y ufw
    
    # Default policies
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH
    sudo ufw allow ssh
    
    # Allow application ports
    sudo ufw allow 3000/tcp   # Frontend
    sudo ufw allow 8001/tcp   # Backend API
    
    # Enable firewall
    sudo ufw --force enable
    
    print_status "Firewall configured ✓"
    print_status "Allowed ports: SSH, 3000 (Frontend), 8001 (Backend)"
}

# Create management scripts
create_scripts() {
    print_header "Creating Management Scripts"
    
    # Start script
    cat > ~/bitcoin-bens-club/scripts/start.sh << 'EOF'
#!/bin/bash
echo "🍔 Starting Bitcoin Ben's Burger Bus Club..."

# Start backend
sudo systemctl start bbc-backend

# Start frontend with PM2
cd ~/bitcoin-bens-club
pm2 start config/pm2-frontend.json

echo "✅ Services started!"
echo "Frontend: http://$(hostname -I | awk '{print $1}'):3000"
echo "Backend API: http://$(hostname -I | awk '{print $1}'):8001"
echo "Admin Panel: http://$(hostname -I | awk '{print $1}'):3000?admin=true"
EOF

    # Stop script
    cat > ~/bitcoin-bens-club/scripts/stop.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping Bitcoin Ben's Burger Bus Club..."

# Stop services
pm2 stop bbc-frontend
sudo systemctl stop bbc-backend

echo "✅ Services stopped!"
EOF

    # Status script
    cat > ~/bitcoin-bens-club/scripts/status.sh << 'EOF'
#!/bin/bash
echo "📊 Bitcoin Ben's Burger Bus Club Status"
echo "======================================"

echo -e "\n🔧 Backend Service:"
sudo systemctl status bbc-backend --no-pager -l

echo -e "\n⚛️  Frontend Service:"
pm2 show bbc-frontend 2>/dev/null || echo "Frontend not running"

echo -e "\n🗄️  MongoDB Status:"
sudo systemctl status mongod --no-pager -l

echo -e "\n💾 Disk Usage:"
df -h /

echo -e "\n🧠 Memory Usage:"
free -h

echo -e "\n🌐 Network Info:"
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo "Local IP: $LOCAL_IP"
echo "Frontend: http://$LOCAL_IP:3000"
echo "Admin: http://$LOCAL_IP:3000?admin=true"
EOF

    # Update script
    cat > ~/bitcoin-bens-club/scripts/update.sh << 'EOF'
#!/bin/bash
echo "🔄 Updating Bitcoin Ben's Burger Bus Club..."

cd ~/bitcoin-bens-club

# Stop services
./scripts/stop.sh

# Backup database
./scripts/backup.sh

# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Node.js packages
cd frontend
yarn install
yarn build

# Update Python packages
cd ../backend
source ../venv/bin/activate
pip install --upgrade -r requirements.txt

# Restart services
./scripts/start.sh

echo "✅ Update complete!"
EOF

    # Backup script
    cat > ~/bitcoin-bens-club/scripts/backup.sh << 'EOF'
#!/bin/bash
echo "💾 Creating backup..."

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=~/bitcoin-bens-club/backups/$BACKUP_DATE

mkdir -p $BACKUP_DIR

# Backup MongoDB
mongodump --db bitcoin_bens_club --out $BACKUP_DIR/mongodb

# Backup configuration
cp -r ~/bitcoin-bens-club/config $BACKUP_DIR/
cp ~/bitcoin-bens-club/backend/.env $BACKUP_DIR/backend_env
cp ~/bitcoin-bens-club/frontend/.env $BACKUP_DIR/frontend_env

# Compress backup
cd ~/bitcoin-bens-club/backups
tar -czf "${BACKUP_DATE}.tar.gz" $BACKUP_DATE
rm -rf $BACKUP_DATE

echo "✅ Backup created: ${BACKUP_DATE}.tar.gz"
EOF

    # Make scripts executable
    chmod +x ~/bitcoin-bens-club/scripts/*.sh
    
    print_status "Management scripts created ✓"
}

# Main installation function
main() {
    print_header "Bitcoin Ben's Burger Bus Club - Pi5 Setup"
    
    # Run installation steps
    check_pi5
    update_system
    install_nodejs
    install_python
    install_mongodb
    setup_directories
    install_app_dependencies
    configure_environment
    setup_services
    setup_firewall
    create_scripts
    
    print_header "Installation Complete!"
    
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    
    echo -e "${GREEN}🎉 Bitcoin Ben's Burger Bus Club is now installed on your Pi5!${NC}\n"
    
    echo "📋 Next Steps:"
    echo "1. Copy your application files (backend/frontend code) to:"
    echo "   ~/bitcoin-bens-club/backend/"
    echo "   ~/bitcoin-bens-club/frontend/"
    echo ""
    echo "2. Start the application:"
    echo "   cd ~/bitcoin-bens-club"
    echo "   ./scripts/start.sh"
    echo ""
    echo "3. Access your application:"
    echo "   Frontend: http://$LOCAL_IP:3000"
    echo "   Admin Panel: http://$LOCAL_IP:3000?admin=true"
    echo "   Backend API: http://$LOCAL_IP:8001"
    echo ""
    echo "4. Admin Credentials:"
    echo "   Email: $ADMIN_EMAIL"
    echo "   Password: [as set during installation]"
    echo ""
    echo "📚 Management Commands:"
    echo "   ./scripts/start.sh    - Start services"
    echo "   ./scripts/stop.sh     - Stop services"  
    echo "   ./scripts/status.sh   - Check status"
    echo "   ./scripts/backup.sh   - Create backup"
    echo "   ./scripts/update.sh   - Update application"
    echo ""
    echo "🔧 For internet access, configure port forwarding on your router:"
    echo "   Port 3000 -> $LOCAL_IP:3000 (Frontend)"
    echo "   Port 8001 -> $LOCAL_IP:8001 (Backend API)"
    echo ""
    print_status "Setup completed successfully! 🍔"
}

# Run main function
main "$@"