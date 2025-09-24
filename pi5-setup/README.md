# Bitcoin Ben's Burger Bus Club - Raspberry Pi 5 Setup

## Complete Installation Guide for Pi5

This guide will help you set up the Bitcoin Ben's Burger Bus Club application natively on your Raspberry Pi 5 with local MongoDB.

## Prerequisites
- Raspberry Pi 5 with Raspberry Pi OS
- Internet connection
- At least 8GB SD card (16GB+ recommended)
- SSH access or direct terminal access

## Quick Setup (Run this first!)

1. **Download the setup files to your Pi5:**
```bash
# Create project directory
mkdir -p ~/bitcoin-bens-club
cd ~/bitcoin-bens-club

# Copy all the setup files to this directory
```

2. **Run the automated setup script:**
```bash
chmod +x setup-pi5.sh
sudo ./setup-pi5.sh
```

3. **Follow the prompts for:**
- Admin email and password setup
- Network configuration
- SSL setup (optional)

## What Gets Installed

### System Dependencies
- Node.js 18.x LTS
- Python 3.11+
- MongoDB 7.0 Community Edition
- PM2 Process Manager
- Nginx (reverse proxy)
- UFW Firewall

### Application Setup
- Backend API server (FastAPI/Python)
- Frontend React application
- MongoDB local database
- Auto-start services
- Log rotation
- Backup scripts

## Network Access Options

### Option 1: Local Network Only
- Access via: `http://your-pi-ip:3000`
- Admin panel: `http://your-pi-ip:3000?admin=true`

### Option 2: Internet Access (Recommended)
- Domain setup with dynamic DNS
- SSL certificate (Let's Encrypt)
- Firewall configuration
- Port forwarding setup guide

## Management Commands

After setup, use these commands:

```bash
# Check application status
sudo systemctl status bbc-backend
sudo systemctl status bbc-frontend

# View logs
sudo journalctl -u bbc-backend -f
sudo journalctl -u bbc-frontend -f

# Restart services
sudo systemctl restart bbc-backend
sudo systemctl restart bbc-frontend

# Update application
cd ~/bitcoin-bens-club
./update-app.sh
```

## File Structure
```
~/bitcoin-bens-club/
├── backend/              # Python FastAPI server
├── frontend/             # React application
├── scripts/              # Management scripts
├── config/               # Configuration files
├── logs/                 # Application logs
├── backups/              # Database backups
└── ssl/                  # SSL certificates
```

## Security Features
- Local MongoDB with authentication
- UFW firewall configuration
- Fail2ban for SSH protection
- Regular security updates
- Database encryption at rest

## Troubleshooting

### Common Issues:
1. **Port conflicts**: Default ports 3000 (frontend), 8001 (backend), 27017 (MongoDB)
2. **Memory issues**: Pi5 needs 4GB+ RAM for optimal performance
3. **Network access**: Check firewall and router port forwarding

### Get Help:
- Check logs: `./check-logs.sh`
- Run diagnostics: `./diagnose.sh`
- View system resources: `htop`

## Backup & Recovery
- Automatic daily MongoDB backups
- Configuration backup
- Easy restore process
- Migration tools included

---

**Next Steps:** Run `./setup-pi5.sh` to begin installation!