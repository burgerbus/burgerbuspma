#!/bin/bash

# Bitcoin Ben's Burger Bus Club - QUICK DEPLOY Script
# Downloads and runs the complete installation automatically

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_banner() {
    echo -e "${YELLOW}"
    cat << 'EOF'
    ╔══════════════════════════════════════════════════════════════╗
    ║  🚀 Bitcoin Ben's Burger Bus Club - QUICK DEPLOY            ║
    ║                                                              ║
    ║  One command to rule them all: Complete Pi5 setup!          ║
    ║  🍔 Production Ready • 🔒 Secure • 🌐 Internet Access      ║
    ╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

print_status() { echo -e "${GREEN}[✓]${NC} $1"; }
print_info() { echo -e "${BLUE}[ℹ]${NC} $1"; }
print_error() { echo -e "${RED}[✗]${NC} $1"; }

main() {
    print_banner
    
    print_info "Starting Bitcoin Ben's Burger Bus Club Quick Deploy..."
    
    # Pre-flight checks
    print_info "Running pre-flight checks..."
    
    # Check if Pi5
    if ! grep -q "Raspberry Pi 5" /proc/cpuinfo 2>/dev/null; then
        print_info "This appears to be running on non-Pi5 hardware - continuing anyway"
    fi
    
    # Check internet connection
    if ! ping -c 1 google.com >/dev/null 2>&1; then
        print_error "No internet connection detected. Please connect to internet and try again."
        exit 1
    fi
    
    # Check if running as regular user with sudo
    if [[ $EUID -eq 0 ]]; then
        print_error "Please run as a regular user with sudo access, not as root!"
        exit 1
    fi
    
    if ! sudo -n true 2>/dev/null; then
        print_error "This script requires sudo access. Please run: sudo visudo"
        print_error "And add: $USER ALL=(ALL) NOPASSWD:ALL"
        exit 1
    fi
    
    print_status "Pre-flight checks passed"
    
    # Create temp directory
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    print_info "Downloading installation package..."
    
    # Download the complete installation script
    if command -v curl >/dev/null 2>&1; then
        curl -sL https://raw.githubusercontent.com/your-repo/bitcoin-bens-club/main/pi5-setup/install.sh -o install.sh
    elif command -v wget >/dev/null 2>&1; then
        wget -q https://raw.githubusercontent.com/your-repo/bitcoin-bens-club/main/pi5-setup/install.sh -O install.sh
    else
        # Fallback: create the installer locally if can't download
        cat > install.sh << 'INSTALL_SCRIPT_HERE'
# The complete install.sh content would be embedded here
# For now, we'll use a placeholder
echo "Installation script would be embedded here"
echo "For manual installation, copy the install.sh from the pi5-complete-package"
exit 1
INSTALL_SCRIPT_HERE
    fi
    
    chmod +x install.sh
    
    print_info "Starting installation..."
    print_info "This may take 15-30 minutes depending on your internet speed"
    
    # Run the installer
    ./install.sh
    
    # Cleanup
    cd /
    rm -rf "$TEMP_DIR"
    
    print_status "Quick deploy completed!"
}

# Show help
show_help() {
    print_banner
    cat << EOF
${BLUE}Bitcoin Ben's Burger Bus Club - Quick Deploy${NC}

${YELLOW}Usage:${NC}
  curl -sSL https://bitcoin-bens.com/quick-deploy.sh | bash
  
${YELLOW}Or manual:${NC}
  wget https://bitcoin-bens.com/quick-deploy.sh
  chmod +x quick-deploy.sh
  ./quick-deploy.sh

${YELLOW}What this installs:${NC}
  ✅ Complete Bitcoin Ben's application stack
  ✅ MongoDB 7.0 with authentication
  ✅ Node.js 18.x LTS + Python 3.11+
  ✅ SSL certificates (Let's Encrypt)
  ✅ VPN access (Tailscale or WireGuard)
  ✅ Enhanced security (UFW + Fail2Ban)
  ✅ System monitoring & alerts
  ✅ Automatic backups
  ✅ Internet access configuration

${YELLOW}Requirements:${NC}
  • Raspberry Pi 5 (or compatible ARM64 device)
  • Raspberry Pi OS (Debian-based)
  • Internet connection
  • User with sudo access (not root)

${YELLOW}Post-install:${NC}
  1. Copy your app files to ~/bitcoin-bens-club/
  2. Run ~/bitcoin-bens-club/complete-setup.sh
  3. Access at http://your-pi-ip:3000

${GREEN}🍔 Ready to serve up some Bitcoin Burgers!${NC}
EOF
}

# Handle arguments
case "${1:-}" in
    -h|--help|help)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac