#!/bin/bash

# Bitcoin Ben's Burger Bus Club - Web Installer
# One-command installation from the internet

set -e

# Styling
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_banner() {
    echo -e "${YELLOW}${BOLD}"
    cat << 'EOF'
    ╔══════════════════════════════════════════════════════════════╗
    ║           🍔 Bitcoin Ben's Burger Bus Club 🍔               ║
    ║                                                              ║
    ║              🚀 ONE-COMMAND INSTALLER 🚀                   ║
    ║                                                              ║
    ║  Production-Ready • SSL Enabled • VPN Support • Monitoring  ║
    ╚══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

print_status() { echo -e "${GREEN}[✓]${NC} $1"; }
print_info() { echo -e "${BLUE}[ℹ]${NC} $1"; }
print_error() { echo -e "${RED}[✗]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; }

# Check prerequisites
check_system() {
    print_info "Checking system compatibility..."
    
    # Check if Debian/Ubuntu based
    if ! command -v apt >/dev/null 2>&1; then
        print_error "This installer requires Debian/Ubuntu based system (apt package manager)"
        exit 1
    fi
    
    # Check internet connection
    if ! ping -c 1 google.com >/dev/null 2>&1; then
        print_error "Internet connection required for installation"
        exit 1
    fi
    
    # Check sudo access
    if [[ $EUID -eq 0 ]]; then
        print_error "Don't run as root! Use a regular user with sudo access"
        exit 1
    fi
    
    if ! sudo -n true 2>/dev/null; then
        print_error "Sudo access required. Please ensure your user has sudo privileges"
        exit 1
    fi
    
    # Check available space (need at least 2GB)
    AVAILABLE_SPACE=$(df / | tail -1 | awk '{print $4}')
    if [[ $AVAILABLE_SPACE -lt 2000000 ]]; then
        print_warning "Low disk space detected. At least 2GB recommended"
    fi
    
    print_status "System compatibility check passed"
}

# Download and extract package
download_package() {
    print_info "Downloading Bitcoin Ben's installation package..."
    
    cd ~
    
    # Create temp directory
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    # Try to download from GitHub releases or fallback
    DOWNLOAD_URL="https://github.com/bitcoin-bens/pi5-setup/releases/latest/download/bitcoin-bens-pi5-complete.tar.gz"
    
    if command -v curl >/dev/null 2>&1; then
        curl -L -o package.tar.gz "$DOWNLOAD_URL" || {
            print_warning "GitHub download failed, trying alternative source..."
            curl -L -o package.tar.gz "https://bitcoin-bens.com/releases/latest.tar.gz" || {
                print_error "Download failed. Please check internet connection"
                exit 1
            }
        }
    elif command -v wget >/dev/null 2>&1; then
        wget -O package.tar.gz "$DOWNLOAD_URL" || {
            print_warning "GitHub download failed, trying alternative source..."
            wget -O package.tar.gz "https://bitcoin-bens.com/releases/latest.tar.gz" || {
                print_error "Download failed. Please check internet connection"
                exit 1
            }
        }
    else
        print_error "Neither curl nor wget found. Please install one of them"
        exit 1
    fi
    
    print_status "Package downloaded successfully"
    
    # Extract package
    print_info "Extracting installation files..."
    tar -xzf package.tar.gz
    
    # Find the extracted directory
    PACKAGE_DIR=$(find . -maxdepth 1 -type d -name "bitcoin-bens-pi5-complete*" | head -1)
    if [[ -z "$PACKAGE_DIR" ]]; then
        print_error "Failed to extract package properly"
        exit 1
    fi
    
    cd "$PACKAGE_DIR"
    print_status "Installation files extracted"
}

# Run installation
run_installation() {
    print_info "Starting Bitcoin Ben's installation..."
    
    # Make installer executable
    chmod +x setup/install.sh setup/*.sh
    
    # Run the main installer
    ./setup/install.sh
    
    print_status "Installation completed!"
}

# Cleanup
cleanup() {
    print_info "Cleaning up temporary files..."
    cd ~
    rm -rf "$TEMP_DIR"
    print_status "Cleanup completed"
}

# Show completion message
show_completion() {
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    
    echo ""
    echo -e "${GREEN}${BOLD}🎉 Bitcoin Ben's Burger Bus Club Installation Complete! 🎉${NC}"
    echo ""
    echo -e "${BOLD}📱 Access Your Application:${NC}"
    echo -e "   • Frontend:     ${BLUE}http://$LOCAL_IP:3000${NC}"
    echo -e "   • Admin Panel:  ${BLUE}http://$LOCAL_IP:3000?admin=true${NC}"  
    echo -e "   • API Docs:     ${BLUE}http://$LOCAL_IP:8001/docs${NC}"
    echo ""
    echo -e "${BOLD}🛠️ Management Commands:${NC}"
    echo -e "   • Status:  ${YELLOW}~/bitcoin-bens-club/scripts/status.sh${NC}"
    echo -e "   • Start:   ${YELLOW}~/bitcoin-bens-club/scripts/start.sh${NC}"
    echo -e "   • Stop:    ${YELLOW}~/bitcoin-bens-club/scripts/stop.sh${NC}"
    echo -e "   • Backup:  ${YELLOW}~/bitcoin-bens-club/scripts/backup.sh${NC}"
    echo ""
    echo -e "${BOLD}📊 Monitoring:${NC}"
    echo -e "   • Logs:    ${YELLOW}tail -f ~/bitcoin-bens-club/logs/*.log${NC}"
    echo -e "   • Monitor: ${YELLOW}pm2 monit${NC}"
    echo -e "   • System:  ${YELLOW}htop${NC}"
    echo ""
    echo -e "${GREEN}🍔 Your Bitcoin Ben's Burger Bus Club is now ready to serve! 🚀${NC}"
    echo ""
    
    if [[ -f ~/bitcoin-bens-club/scripts/status.sh ]]; then
        echo -e "${BLUE}Running initial status check...${NC}"
        ~/bitcoin-bens-club/scripts/status.sh
    fi
}

# Main installation function
main() {
    print_banner
    
    echo -e "${BLUE}This installer will set up Bitcoin Ben's Burger Bus Club on your Pi5${NC}"
    echo -e "${BLUE}with complete production features including SSL, VPN, and monitoring.${NC}"
    echo ""
    
    read -p "Continue with installation? (y/N): " CONTINUE
    [[ ! $CONTINUE =~ ^[Yy]$ ]] && { echo "Installation cancelled."; exit 0; }
    
    echo ""
    print_info "Starting Bitcoin Ben's one-command installation..."
    
    check_system
    download_package
    run_installation
    cleanup
    show_completion
}

# Show help
show_help() {
    print_banner
    cat << EOF
${BLUE}Bitcoin Ben's Burger Bus Club - Web Installer${NC}

${YELLOW}Usage:${NC}
  curl -sSL https://bitcoin-bens.com/install | bash
  
${YELLOW}Or:${NC}
  wget -qO- https://bitcoin-bens.com/install | bash

${YELLOW}Features Installed:${NC}
  ✅ Complete Bitcoin Ben's application
  ✅ MongoDB 7.0 with authentication  
  ✅ SSL certificates (Let's Encrypt)
  ✅ VPN support (Tailscale/WireGuard)
  ✅ Enhanced security (UFW + Fail2Ban)
  ✅ System monitoring & alerts
  ✅ Automated backups
  ✅ Management scripts

${YELLOW}Requirements:${NC}
  • Raspberry Pi 5 (or compatible ARM64 device)
  • Debian/Ubuntu-based OS
  • Internet connection
  • User with sudo access (not root)
  • 2GB+ available disk space

${YELLOW}Access After Install:${NC}
  • App: http://your-pi-ip:3000
  • Admin: http://your-pi-ip:3000?admin=true
  • API: http://your-pi-ip:8001

${GREEN}Ready to serve Bitcoin Burgers worldwide! 🍔${NC}
EOF
}

# Handle command line arguments
case "${1:-}" in
    -h|--help|help)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac