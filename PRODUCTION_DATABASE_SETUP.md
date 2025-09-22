# Production Database Setup Guide

## MongoDB Atlas Setup for Bitcoin Ben's Burger Bus Club

### Step 1: Create MongoDB Atlas Account
1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Sign up for a free account
3. Create a new project called "Bitcoin Ben's Burger Bus Club"

### Step 2: Create a Free Cluster
1. Click "Create a Cluster"
2. Choose **M0 Sandbox** (FREE tier - 512MB storage)
3. Select a cloud provider and region (AWS/Google/Azure)
4. Give your cluster a name like "bitcoin-bens-cluster"
5. Click "Create Cluster" (takes 3-5 minutes)

### Step 3: Create Database User
1. Go to "Database Access" in the left sidebar
2. Click "Add New Database User"
3. Choose "Password" authentication
4. Username: `admin_user` (or your preference)
5. Password: Generate a secure password and SAVE IT
6. Database User Privileges: Select "Read and write to any database"
7. Click "Add User"

### Step 4: Configure Network Access
1. Go to "Network Access" in the left sidebar
2. Click "Add IP Address"
3. For development/testing: Click "Allow Access from Anywhere" (0.0.0.0/0)
4. For production: Add your specific deployment IPs
5. Click "Confirm"

### Step 5: Get Connection String
1. Go to "Clusters" in the left sidebar
2. Click "Connect" on your cluster
3. Choose "Connect your application"
4. Driver: **Python**, Version: **3.6 or later**
5. Copy the connection string - it looks like:
   ```
   mongodb+srv://admin_user:<password>@bitcoin-bens-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

### Step 6: Update Environment Variables

**Replace this in your `/app/backend/.env` file:**

```bash
# OLD (localhost - won't work in production)
MONGO_URL="mongodb://localhost:27017"

# NEW (production MongoDB Atlas)
MONGO_URL="mongodb+srv://admin_user:YOUR_PASSWORD@bitcoin-bens-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority"
```

**Important Notes:**
- Replace `YOUR_PASSWORD` with the actual password you created
- Replace `xxxxx` with your actual cluster identifier
- Keep the database name as `bitcoin_bens_burger_club`

### Step 7: Test the Connection
1. After updating `.env`, restart your backend:
   ```bash
   sudo supervisorctl restart backend
   ```
2. Check the logs for successful connection:
   ```bash
   tail -f /var/log/supervisor/backend.out.log
   ```
3. You should see: `✅ MongoDB connected to database: bitcoin_bens_burger_club`

### Step 8: Verify Data Structure
Your production database will automatically create these collections:
- `members` - User accounts and profiles
- `menu_items` - Restaurant menu with multi-currency pricing
- `locations` - Food truck locations
- `events` - Member events
- `orders` - Order history
- `affiliate_referrals` - Referral tracking
- `payment_requests_db` - Payment tracking

### Production Benefits:
✅ **24/7 Uptime** - Professional cloud hosting
✅ **Automatic Backups** - Built-in data protection
✅ **Security** - Encrypted connections and authentication
✅ **Scalability** - Can grow with your user base
✅ **Monitoring** - Performance metrics and alerts

### Free Tier Limits:
- 512MB storage (plenty for thousands of members)
- Shared RAM and processing
- Basic support

### Next Steps After Setup:
1. Update your environment variables with the Atlas connection string
2. Restart your backend service
3. Deploy your application to production
4. Test admin panel, member registration, and BBC token staking

### Security Best Practices:
1. Use strong passwords for database users
2. Restrict network access to specific IPs when possible
3. Enable authentication and use encrypted connections
4. Regularly monitor database activity

Your Bitcoin Ben's Burger Bus Club app will be production-ready with this database setup!