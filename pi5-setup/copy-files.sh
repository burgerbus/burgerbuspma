#!/bin/bash

# Bitcoin Ben's Burger Bus Club - Copy Application Files to Pi5
# Run this script after setup-pi5.sh to copy the actual application code

echo "📁 Copying Application Files to Pi5..."
echo "===================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if target directories exist
if [ ! -d ~/bitcoin-bens-club ]; then
    echo "❌ Bitcoin Ben's Club directory not found. Run setup-pi5.sh first!"
    exit 1
fi

print_status "Copying backend files..."

# Copy backend files
cp -r backend/* ~/bitcoin-bens-club/backend/ 2>/dev/null || {
    print_warning "Backend source not found in current directory"
    echo "Make sure you're running this from the directory containing backend/ and frontend/"
}

print_status "Copying frontend files..."

# Copy frontend files (excluding node_modules and build)
rsync -av --exclude 'node_modules' --exclude 'build' frontend/ ~/bitcoin-bens-club/frontend/ 2>/dev/null || {
    print_warning "Frontend source not found in current directory"
    echo "Make sure you're running this from the directory containing backend/ and frontend/"
}

print_status "Setting up backend environment..."

# Copy environment file and update for Pi5
if [ -f ~/bitcoin-bens-club/backend/.env ]; then
    # Update MongoDB URL for local instance
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    
    # Update backend .env for Pi5
    sed -i "s|MONGO_URL=.*|MONGO_URL=\"mongodb://localhost:27017/bitcoin_bens_club\"|" ~/bitcoin-bens-club/backend/.env
    sed -i "s|REACT_APP_BACKEND_URL=.*|REACT_APP_BACKEND_URL=http://${LOCAL_IP}:8001|" ~/bitcoin-bens-club/frontend/.env
    
    print_status "Environment files updated for Pi5"
fi

print_status "Installing dependencies..."

# Install backend dependencies
cd ~/bitcoin-bens-club/backend
source ../venv/bin/activate
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
yarn install

# Build frontend for production
yarn build

print_status "Files copied and dependencies installed ✅"
print_status "Run './scripts/start.sh' to start the application!"