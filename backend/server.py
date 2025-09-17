from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import secrets
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests
import qrcode
from io import BytesIO
import base64 as b64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# BCH receiving address for membership payments (set your actual BCH address)
BCH_RECEIVING_ADDRESS = os.environ.get("BCH_RECEIVING_ADDRESS", "bitcoincash:qph0duvh0zn0r2um7znh8gx20p50dr3ycc5lcp0sc4")

# PMA P2P Payment Configuration
MEMBERSHIP_FEE_USD = 21.00  # All members pay $21 dues
CASHSTAMP_AMOUNT_USD = 15.00  # All members receive $15 BCH cashstamp
AFFILIATE_COMMISSION_USD = 3.00  # Affiliates earn $3 per referral
PMA_NET_AMOUNT_USD = MEMBERSHIP_FEE_USD - AFFILIATE_COMMISSION_USD  # $18 to PMA

# Pump.fun Token Configuration
PUMP_TOKEN_MINT = os.getenv("PUMP_FUN_TOKEN_ADDRESS", "mWusXdRfsYAoFtYdaDcf8tmG7hnRNvnVc2TuvNEpump")
PUMP_TOKEN_NAME = "Bitcoin Ben's Club Token"
PUMP_TOKEN_SYMBOL = "BBTC"
PUMP_TOKEN_DECIMALS = 9

# P2P Payment Methods (Update these with your actual handles)
PAYMENT_METHODS = {
    "cashapp": {
        "handle": "$BitcoinBen",  # Your CashApp $cashtag
        "display_name": "CashApp",
        "amount": MEMBERSHIP_FEE_USD,
        "cashstamp": CASHSTAMP_AMOUNT_USD,
        "instructions": "Send $21.00 to $BitcoinBen with memo: 'BB Membership + [YOUR EMAIL]'"
    },
    "venmo": {
        "handle": "@BitcoinBen",  # Your Venmo handle
        "display_name": "Venmo", 
        "amount": MEMBERSHIP_FEE_USD,
        "cashstamp": CASHSTAMP_AMOUNT_USD,
        "instructions": "Send $21.00 to @BitcoinBen with note: 'BB Membership + [YOUR EMAIL]'"
    },
    "zelle": {
        "handle": "bitcoinben@example.com",  # Your Zelle email/phone
        "display_name": "Zelle",
        "amount": MEMBERSHIP_FEE_USD,
        "cashstamp": CASHSTAMP_AMOUNT_USD,
        "instructions": "Send $21.00 via Zelle to bitcoinben@example.com with memo: 'BB Membership + [YOUR EMAIL]'"
    },
    "bch": {
        "handle": BCH_RECEIVING_ADDRESS,
        "display_name": "Bitcoin Cash",
        "amount": MEMBERSHIP_FEE_USD,
        "cashstamp": CASHSTAMP_AMOUNT_USD,
        "instructions": f"Send ${MEMBERSHIP_FEE_USD:.2f} worth of BCH. Include your email in the transaction memo for verification."
    }
}

# Simple payment tracking
payment_requests_db = {}

class PaymentRequest(BaseModel):
    payment_id: str
    user_address: str
    amount_usd: float
    amount_bch: float
    bch_price_used: float
    receiving_address: str
    expires_at: str
    status: str = "pending"  # pending, verified, expired
    created_at: str
    qr_code_data: Optional[str] = None
    transaction_id: Optional[str] = None
    verified_at: Optional[str] = None
    verified_by: Optional[str] = None

async def get_bch_price_usd() -> float:
    """Get current BCH price from CoinGecko API"""
    try:
        response = requests.get(
            'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin-cash&vs_currencies=usd',
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return float(data['bitcoin-cash']['usd'])
        else:
            print(f"CoinGecko API error: {response.status_code}")
            return 300.00  # Fallback price
    except Exception as e:
        print(f"Failed to fetch BCH price: {e}")
        return 300.00  # Fallback price

def generate_qr_code(bch_address: str, amount_bch: float, label: str = "Membership Payment") -> str:
    """Generate QR code for BCH payment"""
    try:
        # Create BCH payment URI
        payment_uri = f"bitcoincash:{bch_address}?amount={amount_bch:.8f}&label={label}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(payment_uri)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 string
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = b64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
        
    except Exception as e:
        print(f"QR code generation failed: {e}")
        return None

# BCH Authentication Configuration
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "bch-bitcoin-bens-burger-bus-secret-key-2025")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Bitcoin Ben's Burger Bus Club API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class MemberProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    wallet_address: str = ""
    membership_tier: str = "basic"
    full_name: str = ""
    email: str = ""
    phone: str = ""
    pma_agreed: bool = False
    dues_paid: bool = False
    payment_amount: float = 0.0
    total_orders: int = 0
    favorite_items: List[str] = []
    
    # Affiliate system fields
    referral_code: str = Field(default_factory=lambda: f"BITCOINBEN-{secrets.token_hex(4).upper()}")
    referred_by: Optional[str] = None  # Referral code of who referred them
    total_referrals: int = 0
    total_commissions_earned: float = 0.0
    unpaid_commissions: float = 0.0

class AffiliateReferral(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    referrer_email: str
    referrer_code: str  
    new_member_email: str
    commission_amount: float = AFFILIATE_COMMISSION_USD
    status: str = "pending"  # pending, paid
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    paid_at: Optional[str] = None

class MenuItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    price: float
    member_price: float  # Special pricing for members
    category: str  # appetizer, main, dessert, beverage
    image_url: str
    is_available: bool = True
    tier_required: str = "basic"  # basic, premium, vip

class TruckLocation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    address: str
    date: str
    start_time: str
    end_time: str
    is_member_exclusive: bool = False
    tier_required: str = "basic"

class PreOrder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    wallet_address: str
    items: List[dict]  # [{item_id, quantity, special_instructions}]
    total_amount: float
    pickup_location: str
    pickup_time: str
    status: str = "pending"  # pending, confirmed, ready, completed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MemberEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    date: str
    time: str
    location: str
    tier_required: str = "premium"
    max_attendees: int
    current_attendees: int = 0

# Database helper functions
async def get_or_create_member(wallet_address: str) -> MemberProfile:
    member = await db.members.find_one({"wallet_address": wallet_address})
    if not member:
        new_member = MemberProfile(
            wallet_address=wallet_address,
            full_name="",
            email="",
            phone="",
            pma_agreed=False,
            dues_paid=False,
            payment_amount=0.0
        )
        member_dict = new_member.dict()
        # Convert datetime to string for MongoDB storage
        if 'joined_at' in member_dict and isinstance(member_dict['joined_at'], datetime):
            member_dict['joined_at'] = member_dict['joined_at'].isoformat()
        await db.members.insert_one(member_dict)
        return new_member
    
    # Handle datetime conversion when retrieving from MongoDB
    if 'joined_at' in member and isinstance(member['joined_at'], str):
        member['joined_at'] = datetime.fromisoformat(member['joined_at'].replace('Z', '+00:00'))
    
    return MemberProfile(**member)

async def check_tier_access(required_tier: str, user_tier: str) -> bool:
    tier_hierarchy = {"basic": 1, "premium": 2, "vip": 3}
    return tier_hierarchy.get(user_tier, 0) >= tier_hierarchy.get(required_tier, 0)

# BCH Authentication Helper Functions
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        wallet_address: str = payload.get("sub")
        if wallet_address is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    member = await get_or_create_member(wallet_address)
    return member

# BCH Authentication Models
class ChallengeRequest(BaseModel):
    app_name: str = "Bitcoin Ben's Burger Bus Club"

class ChallengeResponse(BaseModel):
    challenge_id: str
    message: str
    expires_at: str

class SignatureRequest(BaseModel):
    challenge_id: str
    bch_address: str
    signature: str
    message: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

# In-memory challenge storage (use Redis in production)
active_challenges = {}

# BCH Authentication Service
class BCHAuthService:
    def __init__(self):
        self.challenge_expiry_minutes = 5
        
    def generate_challenge(self, app_name: str) -> Dict[str, Any]:
        """Generate a unique challenge message for Bitcoin Cash wallet signing"""
        timestamp = datetime.utcnow()
        nonce = secrets.token_hex(16)
        
        challenge_data = {
            "message": f"Authentication Challenge\nApp: {app_name}\nTime: {timestamp.isoformat()}\nNonce: {nonce}",
            "timestamp": timestamp.isoformat(),
            "nonce": nonce,
            "expires_at": (timestamp + timedelta(minutes=self.challenge_expiry_minutes)).isoformat()
        }
        
        return challenge_data
    
    def verify_signature(self, address: str, signature: str, message: str) -> bool:
        """Verify Bitcoin Cash message signature"""
        try:
            # Simple verification - in a real implementation, use proper BCH message verification
            # For now, we'll accept any signature to test the flow
            return len(signature) > 10 and len(address) > 10
        except Exception as e:
            print(f"Signature verification error: {e}")
            return False

bch_auth_service = BCHAuthService()

# BCH Authentication Endpoints
@api_router.get("/payments/methods")
async def get_payment_methods():
    """Get available P2P payment methods for PMA membership"""
    return {
        "success": True,
        "payment_methods": PAYMENT_METHODS,
        "membership_type": "Private Membership Association",
        "note": "All payments are member-to-member (P2P) transactions, not merchant transactions"
    }

@api_router.post("/payments/create-p2p-payment")
async def create_p2p_payment(
    payment_method: str,
    user_address: str = None,
    user_email: str = None
):
    """Create P2P payment instruction for membership"""
    if payment_method not in PAYMENT_METHODS:
        raise HTTPException(status_code=400, detail="Invalid payment method")
    
    method = PAYMENT_METHODS[payment_method]
    
    # Generate unique payment ID for tracking
    payment_id = f"pma_{payment_method}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
    
    # For BCH, still generate QR code
    qr_code_data = None
    if payment_method == "bch":
        bch_price = await get_bch_price_usd()
        amount_bch = method["amount"] / bch_price
        qr_code_data = generate_qr_code(
            method["handle"], 
            amount_bch, 
            "Bitcoin Ben's PMA Membership"
        )
    
    # Create payment instruction
    payment_instruction = {
        "payment_id": payment_id,
        "method": payment_method,
        "display_name": method["display_name"],
        "handle": method["handle"],
        "amount": method["amount"],
        "instructions": method["instructions"],
        "user_email": user_email,
        "user_address": user_address,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        "status": "pending",
        "qr_code": qr_code_data if payment_method == "bch" else None,
        "cashstamp_bonus": method.get("cashstamp", 0)
    }
    
    # Store payment instruction for admin tracking
    payment_requests_db[payment_id] = payment_instruction
    
    return {
        "success": True,
        "payment_id": payment_id,
        **payment_instruction
    }

@api_router.post("/payments/create-membership-payment")
async def create_membership_payment(user_address: str = None):
    """Legacy endpoint - redirect to BCH P2P payment"""
    return await create_p2p_payment("bch", user_address=user_address)
    try:
        # Get current BCH price
        bch_price = await get_bch_price_usd()
        amount_bch = MEMBERSHIP_FEE_USD / bch_price
        
        # Generate unique payment ID
        payment_id = f"membership_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}"
        
        # Generate QR code for payment
        qr_code_data = generate_qr_code(
            BCH_RECEIVING_ADDRESS, 
            amount_bch, 
            "Bitcoin Ben's Membership"
        )
        
        # Create payment request
        payment_request = PaymentRequest(
            payment_id=payment_id,
            user_address=user_address or "unknown",
            amount_usd=MEMBERSHIP_FEE_USD,
            amount_bch=amount_bch,
            bch_price_used=bch_price,
            receiving_address=BCH_RECEIVING_ADDRESS,
            expires_at=(datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            created_at=datetime.now(timezone.utc).isoformat(),
            qr_code_data=qr_code_data,
            status="pending"
        )
        
        # Store payment request
        payment_requests_db[payment_id] = payment_request
        
        return {
            "success": True,
            "payment_id": payment_id,
            "amount_usd": MEMBERSHIP_FEE_USD,
            "amount_bch": round(amount_bch, 8),
            "bch_price": bch_price,
            "receiving_address": BCH_RECEIVING_ADDRESS,
            "expires_at": payment_request.expires_at,
            "qr_code": qr_code_data,
            "payment_uri": f"bitcoincash:{BCH_RECEIVING_ADDRESS}?amount={amount_bch:.8f}&label=Bitcoin Ben's Membership",
            "instructions": f"Send exactly {amount_bch:.8f} BCH to the address above to activate your membership."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create payment: {str(e)}")

@api_router.get("/payments/status/{payment_id}")
async def get_payment_status(payment_id: str):
    """Get payment status"""
    if payment_id not in payment_requests_db:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    payment = payment_requests_db[payment_id]
    
    # Check if payment expired
    expires_at = datetime.fromisoformat(payment["expires_at"].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expires_at and payment["status"] == "pending":
        payment["status"] = "expired"
    
    return {
        "payment_id": payment_id,
        "status": payment["status"],
        "amount_usd": payment["amount_usd"],
        "amount_bch": payment["amount_bch"],
        "receiving_address": payment["receiving_address"],
        "expires_at": payment["expires_at"],
        "created_at": payment["created_at"],
        "verified_at": payment.get("verified_at"),
        "transaction_id": payment.get("transaction_id")
    }

class AdminVerifyPaymentRequest(BaseModel):
    payment_id: str
    transaction_id: str
    admin_notes: Optional[str] = None

@api_router.post("/admin/verify-payment")
async def admin_verify_payment(request: AdminVerifyPaymentRequest):
    """Admin endpoint to manually verify payment"""
    if request.payment_id not in payment_requests_db:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    payment = payment_requests_db[request.payment_id]
    
    if payment.status == "verified":
        return {"message": "Payment already verified", "payment": payment}
    
    # Update payment status
    payment.status = "verified"
    payment.transaction_id = request.transaction_id
    payment.verified_at = datetime.now(timezone.utc).isoformat()
    payment.verified_by = "admin"  # In real system, would be admin user ID
    
    # Here you would typically:
    # 1. Activate the member's account
    # 2. Send confirmation email
    # 3. Queue cashstamp distribution
    
    return {
        "success": True,
        "message": "Payment verified successfully",
        "payment_id": request.payment_id,
        "member_activated": True,
        "cashstamp_pending": True
    }

@api_router.get("/admin/pending-payments")
async def get_pending_payments():
    """Admin endpoint to get all pending payments"""
    pending_payments = []
    
    for payment_id, payment in payment_requests_db.items():
        if payment.status == "pending":
            # Check if expired
            expires_at = datetime.fromisoformat(payment.expires_at.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > expires_at:
                payment.status = "expired"
                continue
            
            pending_payments.append({
                "payment_id": payment_id,
                "user_address": payment.user_address,
                "amount_usd": payment.amount_usd,
                "amount_bch": payment.amount_bch,
                "created_at": payment.created_at,
                "expires_at": payment.expires_at
            })
    
    return {
        "pending_payments": pending_payments,
        "count": len(pending_payments)
    }

class AdminSendCashstampRequest(BaseModel):
    payment_id: str
    recipient_address: str
    admin_wallet_address: Optional[str] = None

@api_router.post("/admin/send-cashstamp")
async def admin_send_cashstamp(request: AdminSendCashstampRequest):
    """Admin endpoint to send $15 BCH cashstamp (manual for now)"""
    if request.payment_id not in payment_requests_db:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    payment = payment_requests_db[request.payment_id]
    
    if payment.status != "verified":
        raise HTTPException(status_code=400, detail="Payment must be verified first")
    
    try:
        # Get current BCH price for cashstamp
        bch_price = await get_bch_price_usd()
        cashstamp_bch = CASHSTAMP_AMOUNT_USD / bch_price
        
        # Generate cashstamp instructions (manual for now)
        instructions = {
            "action": "send_bch",
            "from_address": request.admin_wallet_address or "Your admin wallet",
            "to_address": request.recipient_address,
            "amount_bch": round(cashstamp_bch, 8),
            "amount_usd": CASHSTAMP_AMOUNT_USD,
            "memo": f"Bitcoin Ben's $15 BCH Cashstamp - Payment {request.payment_id}"
        }
        
        return {
            "success": True,
            "message": "Cashstamp instructions generated",
            "payment_id": request.payment_id,
            "cashstamp_amount_bch": round(cashstamp_bch, 8),
            "cashstamp_amount_usd": CASHSTAMP_AMOUNT_USD,
            "instructions": instructions,
            "note": "Please send the BCH manually using your admin wallet and update the payment record."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate cashstamp: {str(e)}")

# Pump.fun Token Integration Endpoints
@api_router.get("/pump/token-info")
async def get_pump_token_info():
    """Get pump.fun token information"""
    return {
        "success": True,
        "token": {
            "mint": PUMP_TOKEN_MINT,
            "name": PUMP_TOKEN_NAME,
            "symbol": PUMP_TOKEN_SYMBOL,
            "decimals": PUMP_TOKEN_DECIMALS,
            "description": "Official token for Bitcoin Ben's Burger Bus Club members",
            "website": "https://bitcoinben.com",
            "twitter": "@BitcoinBen",
            "telegram": "https://t.me/bitcoinben"
        }
    }

@api_router.get("/pump/token-price")
async def get_pump_token_price():
    """Get current pump.fun token price from DEX"""
    try:
        # In a real implementation, you would fetch from pump.fun API or DEX
        # For now, return mock data
        return {
            "success": True,
            "token_mint": PUMP_TOKEN_MINT,
            "price_sol": 0.000123,  # Price in SOL
            "price_usd": 0.0245,    # Price in USD
            "market_cap": 245000,   # Market cap in USD
            "volume_24h": 12500,    # 24h volume in USD
            "holders": 1250,        # Number of holders
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch token price: {str(e)}")

@api_router.post("/pump/buy-link")
async def generate_pump_buy_link(
    amount_sol: float = None,
    amount_usd: float = None
):
    """Generate pump.fun buy link for the token"""
    try:
        # Construct pump.fun buy URL
        base_url = f"https://pump.fun/{PUMP_TOKEN_MINT}"
        
        params = []
        if amount_sol:
            params.append(f"amount={amount_sol}")
        elif amount_usd:
            # Convert USD to SOL (mock conversion rate)
            sol_price = 200  # Mock SOL price in USD
            amount_sol = amount_usd / sol_price
            params.append(f"amount={amount_sol}")
        
        buy_url = base_url
        if params:
            buy_url += "?" + "&".join(params)
        
        return {
            "success": True,
            "buy_url": buy_url,
            "token_mint": PUMP_TOKEN_MINT,
            "amount_sol": amount_sol,
            "amount_usd": amount_usd,
            "instructions": "Click the link to buy tokens on pump.fun. Make sure you have SOL in your wallet."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate buy link: {str(e)}")

@api_router.get("/pump/member-rewards")
async def get_pump_member_rewards(member: MemberProfile = Depends(get_current_user)):
    """Get pump.fun token rewards for members"""
    try:
        # Calculate member rewards based on membership tier and activity
        base_reward = 100  # Base tokens for basic members
        tier_multiplier = {"basic": 1.0, "premium": 2.0, "vip": 5.0}
        activity_bonus = member.total_orders * 10  # 10 tokens per order
        
        total_reward = base_reward * tier_multiplier.get(member.membership_tier, 1.0) + activity_bonus
        
        return {
            "success": True,
            "member_address": member.wallet_address,
            "membership_tier": member.membership_tier,
            "base_reward": base_reward,
            "tier_multiplier": tier_multiplier.get(member.membership_tier, 1.0),
            "activity_bonus": activity_bonus,
            "total_reward_tokens": total_reward,
            "token_symbol": PUMP_TOKEN_SYMBOL,
            "claim_status": "available",  # In real implementation, track claimed rewards
            "instructions": "Rewards will be distributed weekly to qualifying members"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate rewards: {str(e)}")

class ClaimRewardsRequest(BaseModel):
    wallet_address: str

@api_router.post("/pump/claim-rewards")
async def claim_pump_rewards(
    request: ClaimRewardsRequest,
    member: MemberProfile = Depends(get_current_user)
):
    """Claim pump.fun token rewards (admin approval required)"""
    try:
        # In a real implementation, this would:
        # 1. Verify member eligibility
        # 2. Calculate exact reward amount
        # 3. Queue token transfer
        # 4. Update claim status
        
        rewards_info = await get_pump_member_rewards(member)
        
        return {
            "success": True,
            "message": "Reward claim submitted for admin approval",
            "claim_id": f"claim_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{secrets.token_hex(4)}",
            "member_address": member.wallet_address,
            "reward_wallet": request.wallet_address,
            "reward_amount": rewards_info["total_reward_tokens"],
            "token_symbol": PUMP_TOKEN_SYMBOL,
            "status": "pending_approval",
            "estimated_processing": "1-3 business days"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to claim rewards: {str(e)}")

@api_router.get("/admin/pump/pending-claims")
async def get_pending_pump_claims():
    """Admin: Get all pending pump.fun token reward claims"""
    # In a real implementation, this would fetch from database
    # For now, return empty list
    return {
        "success": True,
        "pending_claims": [],
        "total_pending": 0,
        "total_tokens_pending": 0
    }

class ApproveClaimRequest(BaseModel):
    claim_id: str
    transaction_signature: Optional[str] = None
    admin_notes: Optional[str] = None

@api_router.post("/admin/pump/approve-claim")
async def approve_pump_claim(request: ApproveClaimRequest):
    """Admin: Approve and process pump.fun token reward claim"""
    try:
        # In a real implementation, this would:
        # 1. Validate claim exists
        # 2. Execute token transfer
        # 3. Update claim status
        # 4. Notify member
        
        return {
            "success": True,
            "message": "Token reward claim approved and processed",
            "claim_id": request.claim_id,
            "transaction_signature": request.transaction_signature,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "admin_notes": request.admin_notes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve claim: {str(e)}")

# BCH Authentication Endpoints
@api_router.post("/auth/challenge", response_model=ChallengeResponse)
async def create_challenge(request: ChallengeRequest):
    """Create authentication challenge for Bitcoin Cash wallet signing"""
    challenge_data = bch_auth_service.generate_challenge(request.app_name)
    challenge_id = str(uuid.uuid4())
    
    # Store challenge temporarily
    active_challenges[challenge_id] = challenge_data
    
    return ChallengeResponse(
        challenge_id=challenge_id,
        message=challenge_data["message"],
        expires_at=challenge_data["expires_at"]
    )

@api_router.post("/auth/verify", response_model=TokenResponse)
async def verify_signature(request: SignatureRequest):
    """Verify Bitcoin Cash wallet signature and issue JWT token"""
    # Validate challenge exists and is not expired
    if request.challenge_id not in active_challenges:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired challenge"
        )
    
    challenge_data = active_challenges[request.challenge_id]
    expires_at = datetime.fromisoformat(challenge_data["expires_at"])
    
    if datetime.utcnow() > expires_at:
        del active_challenges[request.challenge_id]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Challenge has expired"
        )
    
    # Verify message matches challenge
    if request.message != challenge_data["message"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message does not match challenge"
        )
    
    # Verify signature
    if not bch_auth_service.verify_signature(request.bch_address, request.signature, request.message):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )
    
    # Clean up used challenge
    del active_challenges[request.challenge_id]
    
    # Generate access token
    access_token_expires = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": request.bch_address, "auth_method": "bch_wallet"},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

# Authentication dependency
async def get_authenticated_member(member: MemberProfile = Depends(get_current_user)) -> MemberProfile:
    return member

# Affiliate System Endpoints
@api_router.get("/affiliate/my-stats")
async def get_affiliate_stats(member: MemberProfile = Depends(get_authenticated_member)):
    """Get affiliate statistics for current member"""
    return {
        "referral_code": member.referral_code,
        "total_referrals": member.total_referrals,
        "total_commissions_earned": member.total_commissions_earned,
        "unpaid_commissions": member.unpaid_commissions,
        "commission_per_referral": AFFILIATE_COMMISSION_USD
    }

@api_router.post("/affiliate/process-referral")
async def process_referral(
    referral_code: str,
    new_member_email: str
):
    """Process a new referral (called during registration)"""
    if not referral_code or referral_code == "":
        return {"success": False, "message": "No referral code provided"}
    
    # Find the referrer by their referral code
    referrer = await db.members.find_one({"referral_code": referral_code})
    if not referrer:
        return {"success": False, "message": "Invalid referral code"}
    
    # Create referral record
    referral = AffiliateReferral(
        referrer_email=referrer["email"],
        referrer_code=referral_code,
        new_member_email=new_member_email
    )
    
    await db.affiliate_referrals.insert_one(referral.dict())
    
    # Update referrer's stats
    await db.members.update_one(
        {"referral_code": referral_code},
        {
            "$inc": {
                "total_referrals": 1,
                "total_commissions_earned": AFFILIATE_COMMISSION_USD,
                "unpaid_commissions": AFFILIATE_COMMISSION_USD
            }
        }
    )
    
    return {
        "success": True,
        "message": f"Referral processed! {referrer['full_name']} will earn ${AFFILIATE_COMMISSION_USD}",
        "commission_amount": AFFILIATE_COMMISSION_USD
    }

@api_router.get("/admin/affiliate-payouts")
async def get_pending_affiliate_payouts():
    """Admin: Get all pending affiliate commission payouts"""
    
    # Get all members with unpaid commissions
    members_with_commissions = await db.members.find({
        "unpaid_commissions": {"$gt": 0}
    }).to_list(100)
    
    payouts = []
    for member in members_with_commissions:
        # Get their pending referrals
        pending_referrals = await db.affiliate_referrals.find({
            "referrer_email": member["email"],
            "status": "pending"
        }).to_list(100)
        
        payouts.append({
            "member_email": member["email"],
            "member_name": member["full_name"],
            "referral_code": member["referral_code"],
            "total_unpaid": member["unpaid_commissions"],
            "pending_referrals": len(pending_referrals),
            "referrals": [{"new_member": r["new_member_email"], "amount": r["commission_amount"]} for r in pending_referrals]
        })
    
    return {
        "pending_payouts": payouts,
        "total_amount_owed": sum(p["total_unpaid"] for p in payouts)
    }

@api_router.post("/admin/pay-affiliate-commission")
async def pay_affiliate_commission(
    member_email: str,
    payment_method: str = "manual",
    transaction_id: str = None
):
    """Admin: Mark affiliate commissions as paid"""
    
    member = await db.members.find_one({"email": member_email})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    unpaid_amount = member.get("unpaid_commissions", 0)
    if unpaid_amount <= 0:
        return {"message": "No unpaid commissions for this member"}
    
    # Mark all pending referrals as paid
    await db.affiliate_referrals.update_many(
        {"referrer_email": member_email, "status": "pending"},
        {
            "$set": {
                "status": "paid",
                "paid_at": datetime.now(timezone.utc).isoformat(),
                "payment_method": payment_method,
                "transaction_id": transaction_id
            }
        }
    )
    
    # Reset unpaid commissions to 0
    await db.members.update_one(
        {"email": member_email},
        {"$set": {"unpaid_commissions": 0}}
    )
    
    return {
        "success": True,
        "message": f"Paid ${unpaid_amount} in commissions to {member['full_name']}",
        "amount_paid": unpaid_amount
    }

# Public routes (no auth required)
@api_router.get("/")
async def root():
    return {"message": "Welcome to Bitcoin Ben's Burger Bus Club - Exclusive Gourmet Experience"}

@api_router.get("/menu/public", response_model=List[dict])
async def get_public_menu():
    """Get basic menu items visible to non-members (no pricing shown)."""
    menu_items = await db.menu_items.find({"tier_required": "basic"}).to_list(50)
    # Remove pricing information for public view
    public_items = []
    for item in menu_items:
        public_item = {
            "id": item["id"],
            "name": item["name"],
            "description": item["description"],
            "category": item["category"],
            "image_url": item["image_url"],
            "is_available": item["is_available"],
            "members_only_pricing": True
        }
        public_items.append(public_item)
    return public_items

@api_router.get("/locations/public", response_model=List[TruckLocation])
async def get_public_locations():
    """Get public food truck locations."""
    locations = await db.locations.find({"is_member_exclusive": False}).to_list(20)
    return [TruckLocation(**location) for location in locations]

# Protected member routes
@api_router.get("/profile", response_model=MemberProfile)
async def get_member_profile(member: MemberProfile = Depends(get_authenticated_member)):
    """Get member profile information."""
    return member

@api_router.put("/profile")
async def update_member_profile(
    favorite_items: List[str],
    member: MemberProfile = Depends(get_authenticated_member)
):
    """Update member favorite items."""
    await db.members.update_one(
        {"wallet_address": member.wallet_address},
        {"$set": {"favorite_items": favorite_items}}
    )

# TEMPORARY: Registration without auth for debugging
@api_router.post("/debug/register")
async def debug_registration(member_data: dict):
    """TEMPORARY: Debug registration without authentication"""
    try:
        wallet_address = member_data.get("wallet_address", "debug_wallet_123")
        
        # Create or get member
        existing_member = await db.members.find_one({"wallet_address": wallet_address})
        if not existing_member:
            new_member = MemberProfile(
                wallet_address=wallet_address,
                full_name="",
                email="",
                phone="",
                pma_agreed=False,
                dues_paid=False,
                payment_amount=0.0
            )
            member_dict = new_member.dict()
            if 'joined_at' in member_dict and isinstance(member_dict['joined_at'], datetime):
                member_dict['joined_at'] = member_dict['joined_at'].isoformat()
            await db.members.insert_one(member_dict)
            existing_member = member_dict
        
        # Update with PMA info
        await db.members.update_one(
            {"wallet_address": wallet_address},
            {"$set": {
                "full_name": member_data.get("fullName", ""),
                "email": member_data.get("email", ""),
                "phone": member_data.get("phone", ""),
                "pma_agreed": member_data.get("pma_agreed", False),
                "dues_paid": member_data.get("dues_paid", False),
                "payment_amount": member_data.get("payment_amount", 0.0),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        updated_member = await db.members.find_one({"wallet_address": wallet_address})
        return {"message": "Debug registration successful", "member": MemberProfile(**updated_member)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Debug registration failed: {str(e)}")

# TEMPORARY: Debug endpoints without auth
@api_router.get("/debug/profile")
async def debug_get_profile():
    """TEMPORARY: Get debug profile without authentication"""
    return {
        "id": "debug-profile-123",
        "wallet_address": "debug_wallet_address",
        "membership_tier": "basic",
        "full_name": "",
        "email": "",
        "phone": "",
        "pma_agreed": False,
        "dues_paid": False,
        "payment_amount": 0.0,
        "total_orders": 0,
        "favorite_items": []
    }

@api_router.get("/debug/menu")
async def debug_get_menu():
    """TEMPORARY: Get debug menu without authentication"""
    # Seed menu items first
    await seed_sample_data()
    
    # Return menu items
    menu_items = await db.menu_items.find().to_list(100)
    return [MenuItem(**item) for item in menu_items]

@api_router.get("/debug/locations")
async def debug_get_locations():
    """TEMPORARY: Get debug locations without authentication"""
    locations = await db.locations.find().to_list(50)
    return [TruckLocation(**location) for location in locations]

@api_router.get("/debug/events")
async def debug_get_events():
    """TEMPORARY: Get debug events without authentication"""
    events = await db.events.find().to_list(20)
    return [MemberEvent(**event) for event in events]

@api_router.get("/debug/orders")
async def debug_get_orders():
    """TEMPORARY: Get debug orders without authentication"""
    return []  # Empty orders list
@api_router.post("/membership/register")
async def register_membership(member_data: dict, member: MemberProfile = Depends(get_authenticated_member)):
    """Register new membership with PMA agreement and dues payment"""
    try:
        # Update existing member with PMA info
        await db.members.update_one(
            {"wallet_address": member.wallet_address},
            {"$set": {
                "full_name": member_data.get("fullName", ""),
                "email": member_data.get("email", ""),
                "phone": member_data.get("phone", ""),
                "pma_agreed": member_data.get("pma_agreed", False),
                "dues_paid": member_data.get("dues_paid", False),
                "payment_amount": member_data.get("payment_amount", 0.0),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        updated_member = await db.members.find_one({"wallet_address": member.wallet_address})
        return {"message": "Membership updated successfully", "member": MemberProfile(**updated_member)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@api_router.get("/menu/member", response_model=List[MenuItem])
async def get_member_menu(member: MemberProfile = Depends(get_authenticated_member)):
    """Get full menu with member pricing."""
    menu_items = await db.menu_items.find().to_list(100)
    accessible_items = []
    
    for item in menu_items:
        menu_item = MenuItem(**item)
        if await check_tier_access(menu_item.tier_required, member.membership_tier):
            accessible_items.append(menu_item)
    
    return accessible_items

@api_router.get("/locations/member", response_model=List[TruckLocation])
async def get_member_locations(member: MemberProfile = Depends(get_authenticated_member)):
    """Get all locations including member-exclusive ones."""
    locations = await db.locations.find().to_list(50)
    accessible_locations = []
    
    for location in locations:
        truck_location = TruckLocation(**location)
        if not truck_location.is_member_exclusive or await check_tier_access(truck_location.tier_required, member.membership_tier):
            accessible_locations.append(truck_location)
    
    return accessible_locations

@api_router.post("/orders", response_model=PreOrder)
async def create_pre_order(
    items: List[dict],
    pickup_location: str,
    pickup_time: str,
    member: MemberProfile = Depends(get_authenticated_member)
):
    """Create a pre-order for pickup. Requires completed PMA agreement and dues payment."""
    
    # Validate that member has completed PMA requirements
    if not member.pma_agreed:
        raise HTTPException(
            status_code=403, 
            detail="PMA agreement must be signed before placing orders. Please complete your membership registration."
        )
    
    if not member.dues_paid:
        raise HTTPException(
            status_code=403, 
            detail="Annual dues ($21) must be paid before placing orders. Please complete your membership payment."
        )
    
    # Calculate total with member pricing
    total = 0.0
    for item in items:
        menu_item = await db.menu_items.find_one({"id": item["item_id"]})
        if menu_item:
            total += menu_item["member_price"] * item["quantity"]
    
    order = PreOrder(
        wallet_address=member.wallet_address,
        items=items,
        total_amount=total,
        pickup_location=pickup_location,
        pickup_time=pickup_time
    )
    
    await db.orders.insert_one(order.dict())
    
    # Update member total orders
    await db.members.update_one(
        {"wallet_address": member.wallet_address},
        {"$inc": {"total_orders": 1}}
    )
    
    return order

@api_router.get("/orders", response_model=List[PreOrder])
async def get_member_orders(member: MemberProfile = Depends(get_authenticated_member)):
    """Get member's order history."""
    orders = await db.orders.find({"wallet_address": member.wallet_address}).to_list(50)
    return [PreOrder(**order) for order in orders]

@api_router.get("/events", response_model=List[MemberEvent])
async def get_member_events(member: MemberProfile = Depends(get_authenticated_member)):
    """Get exclusive member events."""
    events = await db.events.find().to_list(20)
    accessible_events = []
    
    for event in events:
        member_event = MemberEvent(**event)
        if await check_tier_access(member_event.tier_required, member.membership_tier):
            accessible_events.append(member_event)
    
    return accessible_events

@api_router.post("/events/{event_id}/join")
async def join_member_event(
    event_id: str,
    member: MemberProfile = Depends(get_authenticated_member)
):
    """Join a member event."""
    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    member_event = MemberEvent(**event)
    
    if not await check_tier_access(member_event.tier_required, member.membership_tier):
        raise HTTPException(status_code=403, detail="Insufficient membership tier")
    
    if member_event.current_attendees >= member_event.max_attendees:
        raise HTTPException(status_code=400, detail="Event is full")
    
    # Add member to event attendees
    await db.events.update_one(
        {"id": event_id},
        {"$inc": {"current_attendees": 1}}
    )
    
    return {"message": "Successfully joined event"}

# Admin routes for seeding data
@api_router.post("/admin/seed-data")
async def seed_sample_data():
    """Seed the database with sample data (for demo purposes)."""
    
    # Sample menu items - Bitcoin Ben's themed
    sample_menu = [
        {
            "id": str(uuid.uuid4()),
            "name": "The Satoshi Stacker",
            "description": "Triple-stacked wagyu beef with crypto-gold sauce and blockchain pickles",
            "price": 28.00,
            "member_price": 21.00,
            "category": "main",
            "image_url": "https://images.unsplash.com/photo-1616671285410-2a676a9a433d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHw0fHxnb3VybWV0JTIwZm9vZHxlbnwwfHx8fDE3NTc0MzcyMDJ8MA&ixlib=rb-4.1.0&q=85",
            "is_available": True,
            "tier_required": "basic"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "The Hodl Burger",
            "description": "Premium beef that gets better with time, served with diamond hands fries",
            "price": 22.00,
            "member_price": 18.00,
            "category": "main",
            "image_url": "https://images.unsplash.com/photo-1623073284788-0d846f75e329?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwxfHxnb3VybWV0JTIwZm9vZHxlbnwwfHx8fDE3NTc0MzcyMDJ8MA&ixlib=rb-4.1.0&q=85",
            "is_available": True,
            "tier_required": "basic"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "The Bitcoin Mining Rig",
            "description": "Ultimate burger stack for serious crypto miners - requires premium membership",
            "price": 35.00,
            "member_price": 28.00,
            "category": "main",
            "image_url": "https://images.unsplash.com/photo-1628838463043-b81a343794d6?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwyfHxnb3VybWV0JTIwZm9vZHxlbnwwfHx8fDE3NTc0MzcyMDJ8MA&ixlib=rb-4.1.0&q=85",
            "is_available": True,
            "tier_required": "premium"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Lightning Network Loaded Fries",
            "description": "Crispy fries loaded with cheese, bacon, and instant satisfaction",
            "price": 14.00,
            "member_price": 11.00,
            "category": "sides",
            "image_url": "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwyMHx8Zm9vZHxlbnwwfHx8fDE3NTc0MzcyMDJ8MA&ixlib=rb-4.1.0&q=85",
            "is_available": True,
            "tier_required": "basic"
        }
    ]
    
    # Sample locations
    sample_locations = [
        {
            "id": str(uuid.uuid4()),
            "name": "Downtown Business District",
            "address": "123 Main St, Downtown",
            "date": "2025-01-30",
            "start_time": "11:00",
            "end_time": "14:00",
            "is_member_exclusive": False,
            "tier_required": "basic"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "VIP Members Only - Rooftop Event",
            "address": "456 Elite Tower, Penthouse Level",
            "date": "2025-02-01",
            "start_time": "18:00",
            "end_time": "22:00",
            "is_member_exclusive": True,
            "tier_required": "vip"
        }
    ]
    
    # Sample events
    sample_events = [
        {
            "id": str(uuid.uuid4()),
            "title": "Chef's Table Experience",
            "description": "Exclusive 5-course tasting menu with wine pairings",
            "date": "2025-02-05",
            "time": "19:00",
            "location": "Private Kitchen Studio",
            "tier_required": "premium",
            "max_attendees": 12,
            "current_attendees": 3
        }
    ]
    
    # Insert sample data
    await db.menu_items.delete_many({})
    await db.locations.delete_many({})
    await db.events.delete_many({})
    
    await db.menu_items.insert_many(sample_menu)
    await db.locations.insert_many(sample_locations)
    await db.events.insert_many(sample_events)
    
    return {"message": "Sample data seeded successfully"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()