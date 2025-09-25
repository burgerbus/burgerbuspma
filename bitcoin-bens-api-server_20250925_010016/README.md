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
