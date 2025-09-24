# Network Setup Guide for Pi5 Internet Access

## Option 1: Router Port Forwarding (Recommended)

### Step 1: Configure Static IP for Pi5
1. Find your Pi5's MAC address:
   ```bash
   ip link show
   ```

2. In your router's admin panel:
   - Go to DHCP settings
   - Add DHCP reservation for Pi5's MAC address
   - Assign a static local IP (e.g., 192.168.1.100)

### Step 2: Port Forwarding Setup
Configure these port forwards in your router:

| Service | External Port | Internal IP | Internal Port | Protocol |
|---------|---------------|-------------|---------------|----------|
| Frontend | 80 or 8080 | 192.168.1.100 | 3000 | TCP |
| Backend API | 8001 | 192.168.1.100 | 8001 | TCP |
| SSH (optional) | 22222 | 192.168.1.100 | 22 | TCP |

### Step 3: Dynamic DNS (Optional)
If you don't have a static IP from your ISP:
1. Sign up for a free DDNS service (NoIP, DuckDNS, etc.)
2. Configure DDNS in your router or use a client on Pi5
3. Get a domain like: `your-name.ddns.net`

## Option 2: VPN Access (More Secure)

### Using Tailscale (Recommended)
1. Install Tailscale on Pi5:
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```

2. Install Tailscale on your devices
3. Access your Pi5 securely from anywhere!

### Using WireGuard
1. Install WireGuard:
   ```bash
   sudo apt install wireguard
   ```

2. Generate keys and configure server
3. Create client configurations

## Option 3: Cloudflare Tunnel (Advanced)

### Free subdomain with Cloudflare
1. Sign up for free Cloudflare account
2. Install cloudflared on Pi5:
   ```bash
   wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
   sudo dpkg -i cloudflared-linux-arm64.deb
   ```

3. Create tunnel:
   ```bash
   cloudflared tunnel create bitcoin-bens
   ```

4. Configure tunnel for your services

## SSL/TLS Setup with Let's Encrypt

### Prerequisites
- Domain name pointing to your IP
- Port 80 accessible from internet

### Install Certbot
```bash
sudo apt install certbot nginx
```

### Generate SSL Certificate
```bash
sudo certbot --nginx -d your-domain.com
```

### Nginx Configuration
Create `/etc/nginx/sites-available/bitcoin-bens`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/bitcoin-bens /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Security Considerations

### Firewall Rules
```bash
# Allow only necessary ports
sudo ufw default deny incoming
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Fail2Ban Setup
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### Regular Updates
```bash
# Add to crontab for automatic updates
sudo crontab -e

# Add this line for weekly updates at 3 AM Sunday
0 3 * * 0 apt update && apt upgrade -y
```

### Monitor Access
```bash
# Check access logs
sudo tail -f /var/log/nginx/access.log

# Monitor failed login attempts  
sudo tail -f /var/log/auth.log
```

## Testing Internet Access

### From External Network:
```bash
# Test frontend
curl -I http://your-domain.com

# Test backend API
curl http://your-domain.com/api/

# Test admin access
curl http://your-domain.com/?admin=true
```

### Port Checking Tools:
- [CanYouSeeMe.org](https://canyouseeme.org/)
- [PortChecker.co](https://portchecker.co/)
- `nmap` from external network

## Troubleshooting

### Common Issues:
1. **Double NAT**: Check if your ISP uses CGNAT
2. **ISP Blocking**: Some ISPs block residential servers
3. **Firewall**: Check both Pi5 UFW and router firewall
4. **DNS Propagation**: Wait 24-48 hours for DNS changes

### Diagnostic Commands:
```bash
# Check if ports are listening
sudo netstat -tlnp

# Test local access
curl http://localhost:3000
curl http://localhost:8001/api/

# Check external IP
curl ifconfig.me

# Test from Pi5 to external
ping 8.8.8.8
```

Choose the option that best fits your technical comfort level and security requirements!