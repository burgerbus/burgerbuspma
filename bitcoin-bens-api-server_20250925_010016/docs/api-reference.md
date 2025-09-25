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
