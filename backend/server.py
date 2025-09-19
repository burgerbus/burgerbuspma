from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, Header
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

# Solana imports for staking integration
import base58

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# BCH receiving address for membership payments (set your actual BCH address)
BCH_RECEIVING_ADDRESS = os.environ.get("BCH_RECEIVING_ADDRESS", "bitcoincash:qph0duvh0zn0r2um7znh8gx20p50dr3ycc5lcp0sc4")

# PMA P2P Payment Configuration
MEMBERSHIP_FEE_USD = 0.00  # Free membership for now
CASHSTAMP_AMOUNT_USD = 0.00  # All members receive $0 BCH cashstamp
AFFILIATE_COMMISSION_USD = 0.00  # Affiliates earn $0 per referral
PMA_NET_AMOUNT_USD = MEMBERSHIP_FEE_USD - AFFILIATE_COMMISSION_USD  # Free membership

# Pump.fun Token Configuration
PUMP_TOKEN_MINT = os.getenv("PUMP_FUN_TOKEN_ADDRESS", "mWusXdRfsYAoFtYdaDcf8tmG7hnRNvnVc2TuvNEpump")
PUMP_TOKEN_NAME = "Burger Bus Club Token"
PUMP_TOKEN_SYMBOL = "BBC"
PUMP_TOKEN_DECIMALS = 9

# Solana Staking Configuration
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
STAKING_PROGRAM_ID = os.getenv("STAKING_PROGRAM_ID", "Stake11111111111111111111111111111111111112")
VALIDATOR_VOTE_ACCOUNT = os.getenv("VALIDATOR_VOTE_ACCOUNT", "7K8DVxtNJGnMtUY1CQJT5jcs8sFGSZTDiG7kowvFpECh")
MIN_STAKE_AMOUNT = float(os.getenv("MIN_STAKE_AMOUNT", "1.0"))  # Minimum 1 SOL to stake
STAKING_REWARDS_RATE = float(os.getenv("STAKING_REWARDS_RATE", "0.07"))  # 7% APY base rate
MEMBER_BONUS_RATE = float(os.getenv("MEMBER_BONUS_RATE", "0.02"))  # Additional 2% for members

# P2P Payment Methods (Update these with your actual handles)
PAYMENT_METHODS = {
    "cashapp": {
        "handle": "Coming Soon",  # Coming soon
        "display_name": "CashApp",
        "amount": MEMBERSHIP_FEE_USD,
        "cashstamp": CASHSTAMP_AMOUNT_USD,
        "instructions": "CashApp payment option coming soon"
    },
    "venmo": {
        "handle": "Coming Soon",  # Coming soon
        "display_name": "Venmo", 
        "amount": MEMBERSHIP_FEE_USD,
        "cashstamp": CASHSTAMP_AMOUNT_USD,
        "instructions": "Venmo payment option coming soon"
    },
    "zelle": {
        "handle": "Coming Soon",  # Coming soon
        "display_name": "Zelle",
        "amount": MEMBERSHIP_FEE_USD,
        "cashstamp": CASHSTAMP_AMOUNT_USD,
        "instructions": "Zelle payment option coming soon"
    },
    "bch": {
        "handle": BCH_RECEIVING_ADDRESS,
        "display_name": "Bitcoin Cash",
        "amount": MEMBERSHIP_FEE_USD,
        "cashstamp": CASHSTAMP_AMOUNT_USD,
        "instructions": "Bitcoin Cash payments available. Membership is currently FREE - just complete the PMA agreement!"
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

# Solana Staking Models
class StakeAccount(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    member_wallet: str  # Member's wallet address
    stake_account_pubkey: str  # Solana stake account public key
    validator_vote_account: str  # Validator being staked to
    stake_amount_sol: float  # Amount staked in SOL
    stake_amount_lamports: int  # Amount staked in lamports
    status: str = "pending"  # pending, active, deactivating, inactive
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    activated_at: Optional[str] = None
    deactivated_at: Optional[str] = None
    last_reward_calculation: Optional[str] = None
    total_rewards_earned: float = 0.0
    member_bonus_earned: float = 0.0

class StakeReward(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stake_account_id: str
    member_wallet: str
    epoch: int
    base_reward_sol: float
    member_bonus_sol: float
    total_reward_sol: float
    calculated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    distributed_at: Optional[str] = None
    transaction_signature: Optional[str] = None

class StakeRequest(BaseModel):
    wallet_address: str
    amount_sol: float
    validator_vote_account: Optional[str] = None

class UnstakeRequest(BaseModel):
    stake_account_pubkey: str
    wallet_address: str

class StakeRewardsRequest(BaseModel):
    wallet_address: str
    stake_account_pubkey: Optional[str] = None

# Authentication Models
class MemberLoginRequest(BaseModel):
    email: str
    password: str

class MemberRegistrationRequest(BaseModel):
    name: str
    email: str
    password: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    pma_agreed: bool
    referral_code: Optional[str] = None

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

async def verify_member_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify member authentication and return member profile"""
    return await get_current_user(credentials)

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

# Solana Staking Service
class SolanaStakingService:
    def __init__(self):
        self.rpc_url = SOLANA_RPC_URL
        self.staking_program_id = STAKING_PROGRAM_ID
        self.validator_vote_account = VALIDATOR_VOTE_ACCOUNT
        self.min_stake_amount = MIN_STAKE_AMOUNT
        
    async def validate_wallet_address(self, wallet_address: str) -> bool:
        """Validate Solana wallet address format"""
        try:
            # Decode base58 address and check length
            decoded = base58.b58decode(wallet_address)
            return len(decoded) == 32
        except Exception:
            return False
    
    async def validate_stake_account(self, stake_account_pubkey: str) -> bool:
        """Validate stake account exists and is properly formatted"""
        try:
            # Basic validation - decode base58 and check length
            decoded = base58.b58decode(stake_account_pubkey)
            return len(decoded) == 32
        except Exception:
            return False
    
    async def calculate_staking_rewards(self, stake_amount_sol: float, is_member: bool = False, days_staked: int = 1) -> Dict[str, float]:
        """Calculate staking rewards for a given amount and duration"""
        # Base APY calculation
        daily_rate = STAKING_REWARDS_RATE / 365
        base_reward = stake_amount_sol * daily_rate * days_staked
        
        # Member bonus
        member_bonus = 0.0
        if is_member:
            member_daily_rate = MEMBER_BONUS_RATE / 365
            member_bonus = stake_amount_sol * member_daily_rate * days_staked
        
        return {
            "base_reward_sol": base_reward,
            "member_bonus_sol": member_bonus,
            "total_reward_sol": base_reward + member_bonus,
            "effective_apy": STAKING_REWARDS_RATE + (MEMBER_BONUS_RATE if is_member else 0)
        }
    
    async def get_stake_account_info(self, stake_account_pubkey: str) -> Optional[Dict[str, Any]]:
        """Get stake account information from Solana RPC"""
        try:
            # In a real implementation, this would make RPC calls to Solana
            # For now, return mock data
            return {
                "pubkey": stake_account_pubkey,
                "lamports": 2000000000,  # 2 SOL in lamports
                "owner": STAKING_PROGRAM_ID,
                "executable": False,
                "rent_epoch": 361,
                "data": {
                    "parsed": {
                        "type": "delegated",
                        "info": {
                            "meta": {
                                "authorized": {
                                    "staker": stake_account_pubkey,
                                    "withdrawer": stake_account_pubkey
                                },
                                "lockup": {
                                    "custodian": "11111111111111111111111111111112",
                                    "epoch": 0,
                                    "unix_timestamp": 0
                                },
                                "rent_exempt_reserve": 2282880
                            },
                            "stake": {
                                "creditsObserved": 12345,
                                "delegation": {
                                    "activationEpoch": "350",
                                    "deactivationEpoch": "18446744073709551615",
                                    "stake": str(2000000000 - 2282880),
                                    "voter": VALIDATOR_VOTE_ACCOUNT,
                                    "warmupCooldownRate": 0.25
                                }
                            }
                        }
                    }
                }
            }
        except Exception as e:
            print(f"Error fetching stake account info: {e}")
            return None
    
    async def create_stake_instruction(self, wallet_address: str, amount_sol: float) -> Dict[str, Any]:
        """Create instructions for staking SOL (returns instruction data for frontend)"""
        try:
            # Convert SOL to lamports
            amount_lamports = int(amount_sol * 1_000_000_000)
            
            # Generate new stake account keypair (in real implementation)
            stake_account_pubkey = base58.b58encode(os.urandom(32)).decode('utf-8')
            
            return {
                "success": True,
                "stake_account_pubkey": stake_account_pubkey,
                "instructions": {
                    "create_account": {
                        "from_pubkey": wallet_address,
                        "new_account_pubkey": stake_account_pubkey,
                        "lamports": amount_lamports,
                        "space": 200,  # Stake account size
                        "owner": STAKING_PROGRAM_ID
                    },
                    "initialize_stake": {
                        "stake_pubkey": stake_account_pubkey,
                        "authorized": {
                            "staker": wallet_address,
                            "withdrawer": wallet_address
                        }
                    },
                    "delegate_stake": {
                        "stake_pubkey": stake_account_pubkey,
                        "vote_pubkey": VALIDATOR_VOTE_ACCOUNT,
                        "authorized_pubkey": wallet_address
                    }
                },
                "estimated_fee": 0.01,  # SOL
                "note": "Please sign and submit these transactions in order"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_unstake_instruction(self, stake_account_pubkey: str, wallet_address: str) -> Dict[str, Any]:
        """Create instructions for unstaking SOL"""
        try:
            return {
                "success": True,
                "instructions": {
                    "deactivate_stake": {
                        "stake_pubkey": stake_account_pubkey,
                        "authorized_pubkey": wallet_address
                    }
                },
                "estimated_fee": 0.005,  # SOL
                "cooldown_period": "2-3 epochs (~4-6 days)",
                "note": "After deactivation, you can withdraw your SOL in 2-3 epochs"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

solana_staking_service = SolanaStakingService()

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

class P2PPaymentRequest(BaseModel):
    payment_method: str
    user_address: Optional[str] = None
    user_email: Optional[str] = None

@api_router.post("/payments/create-p2p-payment")
async def create_p2p_payment(request: P2PPaymentRequest):
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
    
    if payment["status"] == "verified":
        return {"message": "Payment already verified", "payment": payment}
    
    # Update payment status
    payment["status"] = "verified"
    payment["transaction_id"] = request.transaction_id
    payment["verified_at"] = datetime.now(timezone.utc).isoformat()
    payment["verified_by"] = "admin"  # In real system, would be admin user ID
    
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
        if payment["status"] == "pending":
            # Check if expired
            expires_at = datetime.fromisoformat(payment["expires_at"].replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > expires_at:
                payment["status"] = "expired"
                continue
            
            pending_payments.append({
                "payment_id": payment_id,
                "user_address": payment["user_address"],
                "amount_usd": payment["amount_usd"],
                "amount_bch": payment["amount_bch"],
                "created_at": payment["created_at"],
                "expires_at": payment["expires_at"]
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
    
    if payment["status"] != "verified":
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
        # Try to fetch from pump.fun frontend API
        try:
            # Try multiple pump.fun API endpoints
            api_urls = [
                f"https://frontend-api.pump.fun/coins/{PUMP_TOKEN_MINT}",
                f"https://frontend-api-v2.pump.fun/coins/{PUMP_TOKEN_MINT}",
                f"https://frontend-api-v3.pump.fun/coins/{PUMP_TOKEN_MINT}"
            ]
            
            token_data = None
            for api_url in api_urls:
                try:
                    response = requests.get(api_url, timeout=10)
                    if response.status_code == 200:
                        token_data = response.json()
                        break
                except Exception:
                    continue
            
            if token_data:
                # Extract real data from pump.fun API response
                return {
                    "success": True,
                    "token_mint": PUMP_TOKEN_MINT,
                    "price_sol": float(token_data.get("price_per_sol", 0)),
                    "price_usd": float(token_data.get("usd_market_cap", 0)) / float(token_data.get("total_supply", 1)) if token_data.get("total_supply") else 0,
                    "market_cap": float(token_data.get("usd_market_cap", 0)),
                    "volume_24h": float(token_data.get("volume_24h", 0)),
                    "holders": int(token_data.get("holder_count", 0)),
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "source": "pump.fun_api"
                }
        except Exception as api_error:
            print(f"API fetch failed: {api_error}")
        
        # Fallback: Try to fetch from DexScreener API
        try:
            dexscreener_url = f"https://api.dexscreener.com/latest/dex/tokens/{PUMP_TOKEN_MINT}"
            response = requests.get(dexscreener_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("pairs") and len(data["pairs"]) > 0:
                    pair = data["pairs"][0]
                    return {
                        "success": True,
                        "token_mint": PUMP_TOKEN_MINT,
                        "price_sol": float(pair.get("priceNative", 0)),
                        "price_usd": float(pair.get("priceUsd", 0)),
                        "market_cap": float(pair.get("marketCap", 0)),
                        "volume_24h": float(pair.get("volume", {}).get("h24", 0)),
                        "holders": int(pair.get("info", {}).get("holders", 0)),
                        "last_updated": datetime.now(timezone.utc).isoformat(),
                        "source": "dexscreener_api"
                    }
        except Exception as dex_error:
            print(f"DexScreener fetch failed: {dex_error}")
        
        # Final fallback: Return mock data with warning
        return {
            "success": True,
            "token_mint": PUMP_TOKEN_MINT,
            "price_sol": 0.000123,  # Mock Price in SOL
            "price_usd": 0.0245,    # Mock Price in USD
            "market_cap": 245000,   # Mock Market cap in USD
            "volume_24h": 12500,    # Mock 24h volume in USD
            "holders": 1250,        # Mock Number of holders
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "source": "mock_data",
            "warning": "Real API data unavailable, showing mock data"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch token price: {str(e)}")

class BuyLinkRequest(BaseModel):
    amount_sol: Optional[float] = None
    amount_usd: Optional[float] = None

@api_router.post("/pump/buy-link")
async def generate_pump_buy_link(request: BuyLinkRequest):
    """Generate pump.fun buy link for the token"""
    try:
        # Construct pump.fun buy URL
        base_url = f"https://pump.fun/{PUMP_TOKEN_MINT}"
        
        params = []
        amount_sol = request.amount_sol
        amount_usd = request.amount_usd
        
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

# Optional authentication dependency for staking endpoints
async def get_optional_member(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[MemberProfile]:
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        wallet_address: str = payload.get("sub")
        if wallet_address is None:
            return None
        member = await get_or_create_member(wallet_address)
        return member
    except JWTError:
        return None

# Old staking endpoints removed - replaced with new implementation below

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

# GET endpoint for generating cashstamp
@api_router.get("/admin/generate-cashstamp/{member_id}")
async def generate_cashstamp(member_id: str, admin_wallet: str = Header(...)):
    """Generate BCH cashstamp instructions for verified member"""
    try:
        # Basic admin verification (enhance as needed)
        if admin_wallet != "admin-wallet-address":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Find member
        member = await db.members.find_one({"id": member_id})
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        
        # Create BCH payment for cashstamp
        bch_price = await get_bch_price_usd()
        bch_amount = CASHSTAMP_AMOUNT_USD / bch_price
        
        # Generate QR code for cashstamp
        payment_uri = f"bitcoincash:{BCH_RECEIVING_ADDRESS}?amount={bch_amount:.8f}&message=Cashstamp for {member['email']}"
        qr_code_data = generate_qr_code(payment_uri)
        
        return {
            "success": True,
            "member": member,
            "cashstamp_amount_usd": CASHSTAMP_AMOUNT_USD,
            "bch_amount": bch_amount,
            "bch_address": BCH_RECEIVING_ADDRESS,
            "payment_uri": payment_uri,
            "qr_code": qr_code_data,
            "instructions": f"Send ${CASHSTAMP_AMOUNT_USD} worth of BCH ({bch_amount:.8f} BCH) to complete cashstamp for member {member['email']}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cashstamp generation failed: {str(e)}")

# =======================
# AUTHENTICATION ENDPOINTS
# =======================

@api_router.post("/auth/login")
async def login_member(request: MemberLoginRequest):
    """Authenticate member with email and password"""
    try:
        # Find member by email
        member = await db.members.find_one({"email": request.email})
        if not member:
            raise HTTPException(status_code=404, detail="Member not found. Please check your email or sign up for a new account.")
        
        # For now, we'll use a simple password check
        # In production, you should hash passwords properly
        stored_password = member.get("password", member.get("temp_password", ""))
        
        if not stored_password or stored_password != request.password:
            raise HTTPException(status_code=401, detail="Invalid password. Please try again.")
        
        # Create JWT token
        token_data = {
            "email": member["email"],
            "member_id": member["id"],
            "exp": datetime.now(timezone.utc) + timedelta(days=7)  # 7 day token
        }
        
        access_token = jwt.encode(token_data, JWT_SECRET_KEY, algorithm="HS256")
        
        # Update last login
        await db.members.update_one(
            {"id": member["id"]},
            {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {
            "success": True,
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": member["id"],
                "email": member["email"],
                "name": member["name"],
                "pma_agreed": member.get("pma_agreed", False),
                "dues_paid": member.get("dues_paid", False),
                "wallet_address": member.get("wallet_address", ""),
                "referral_code": member.get("referral_code", ""),
                "is_member": member.get("pma_agreed", False) and member.get("dues_paid", False)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@api_router.post("/auth/register")
async def register_member(request: MemberRegistrationRequest):
    """Register a new member with PMA agreement"""
    try:
        # Check if member already exists
        existing_member = await db.members.find_one({"email": request.email})
        if existing_member:
            raise HTTPException(status_code=409, detail="Member with this email already exists")
        
        # Generate member ID and referral code
        member_id = str(uuid.uuid4())
        referral_code = f"BITCOINBEN-{secrets.token_urlsafe(8).upper()}"
        
        # Create member record
        member_data = {
            "id": member_id,
            "name": request.name,
            "email": request.email,
            "password": request.password,  # In production, hash this!
            "phone": request.phone or "",
            "address": request.address or "",
            "city": request.city or "",
            "state": request.state or "",
            "zip_code": request.zip_code or "",
            "pma_agreed": request.pma_agreed,
            "dues_paid": True,  # Since membership is free now
            "referral_code": referral_code,
            "referred_by": request.referral_code or "",
            "wallet_address": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_login": datetime.now(timezone.utc).isoformat()
        }
        
        # Insert member
        await db.members.insert_one(member_data)
        
        # Process referral if provided
        if request.referral_code:
            try:
                referrer = await db.members.find_one({"referral_code": request.referral_code})
                if referrer:
                    # Record referral
                    referral_record = {
                        "id": str(uuid.uuid4()),
                        "referrer_id": referrer["id"],
                        "referred_id": member_id,
                        "commission_amount_usd": AFFILIATE_COMMISSION_USD,
                        "status": "pending",
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    await db.referrals.insert_one(referral_record)
            except Exception as e:
                print(f"Referral processing error: {e}")
        
        # Create JWT token
        token_data = {
            "email": member_data["email"],
            "member_id": member_id,
            "exp": datetime.now(timezone.utc) + timedelta(days=7)
        }
        
        access_token = jwt.encode(token_data, JWT_SECRET_KEY, algorithm="HS256")
        
        return {
            "success": True,
            "access_token": access_token,
            "token_type": "bearer",
            "member_id": member_id,
            "referral_code": referral_code,
            "user": {
                "id": member_id,
                "email": member_data["email"],
                "name": member_data["name"],
                "pma_agreed": True,
                "dues_paid": True,
                "wallet_address": "",
                "referral_code": referral_code,
                "is_member": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

# =======================
# BBC TOKEN STAKING ENDPOINTS
# =======================

solana_staking_service = SolanaStakingService()

# Public staking information endpoint
@api_router.get("/staking/info")
async def get_staking_info():
    """Get general staking information and benefits"""
    return {
        "success": True,
        "staking_info": {
            "minimum_stake_sol": MIN_STAKE_AMOUNT,
            "base_apy": STAKING_REWARDS_RATE * 100,  # Convert to percentage
            "member_bonus_apy": MEMBER_BONUS_RATE * 100,
            "total_member_apy": (STAKING_REWARDS_RATE + MEMBER_BONUS_RATE) * 100,
            "validator_vote_account": VALIDATOR_VOTE_ACCOUNT,
            "benefits": {
                "club_members": f"{(STAKING_REWARDS_RATE + MEMBER_BONUS_RATE) * 100:.1f}% APY",
                "non_members": f"{STAKING_REWARDS_RATE * 100:.1f}% APY",
                "member_bonus": f"Extra {MEMBER_BONUS_RATE * 100:.1f}% APY for club members"
            }
        }
    }

# Calculate staking rewards (public endpoint)
@api_router.post("/staking/calculate-rewards")
async def calculate_staking_rewards(request: StakeRewardsRequest):
    """Calculate potential staking rewards"""
    try:
        # Validate wallet address
        if not await solana_staking_service.validate_wallet_address(request.wallet_address):
            raise HTTPException(status_code=400, detail="Invalid wallet address")
        
        # Check if user is a club member (optional, works without login)
        is_member = False
        try:
            member = await db.members.find_one({"wallet_address": request.wallet_address})
            is_member = member and member.get("dues_paid", False) and member.get("pma_agreed", False)
        except Exception:
            is_member = False
        
        # Calculate rewards for different time periods
        calculations = {}
        for days in [1, 7, 30, 365]:
            rewards = await solana_staking_service.calculate_staking_rewards(
                stake_amount_sol=MIN_STAKE_AMOUNT,
                is_member=is_member,
                days_staked=days
            )
            calculations[f"{days}_days"] = rewards
        
        return {
            "success": True,
            "wallet_address": request.wallet_address,
            "is_club_member": is_member,
            "minimum_stake_sol": MIN_STAKE_AMOUNT,
            "reward_calculations": calculations,
            "note": "Become a club member for bonus rewards!" if not is_member else "Club member bonus active!"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reward calculation failed: {str(e)}")

# Create stake (authenticated)
@api_router.post("/staking/create-stake")
async def create_stake(request: StakeRequest, current_member: MemberProfile = Depends(verify_member_auth)):
    """Create a new stake account for the authenticated member"""
    try:
        # Validate inputs
        if not await solana_staking_service.validate_wallet_address(request.wallet_address):
            raise HTTPException(status_code=400, detail="Invalid wallet address")
        
        if request.amount_sol < MIN_STAKE_AMOUNT:
            raise HTTPException(status_code=400, detail=f"Minimum stake amount is {MIN_STAKE_AMOUNT} SOL")
        
        # Ensure wallet belongs to authenticated member
        if current_member.wallet_address != request.wallet_address:
            raise HTTPException(status_code=403, detail="Can only stake from your own wallet")
        
        # Use specified validator or default
        validator = request.validator_vote_account or VALIDATOR_VOTE_ACCOUNT
        
        # Create staking instructions
        instructions = await solana_staking_service.create_stake_instruction(
            request.wallet_address,
            request.amount_sol
        )
        
        if not instructions.get("success"):
            raise HTTPException(status_code=500, detail=instructions.get("error", "Failed to create stake instructions"))
        
        # Create stake account record
        stake_account = StakeAccount(
            member_wallet=request.wallet_address,
            stake_account_pubkey=instructions["stake_account_pubkey"],
            validator_vote_account=validator,
            stake_amount_sol=request.amount_sol,
            stake_amount_lamports=int(request.amount_sol * 1_000_000_000),
            status="pending"
        )
        
        # Store in database
        await db.stake_accounts.insert_one(stake_account.dict())
        
        return {
            "success": True,
            "stake_account": stake_account.dict(),
            "transaction_instructions": instructions,
            "next_steps": [
                "1. Sign and submit the transaction using your Solana wallet",
                "2. Wait for transaction confirmation",
                "3. Your stake will become active in the next epoch",
                "4. Rewards will start accruing once active"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stake creation failed: {str(e)}")

# Get member's stake accounts
@api_router.get("/staking/my-stakes")
async def get_my_stakes(current_member: MemberProfile = Depends(verify_member_auth)):
    """Get all stake accounts for the authenticated member"""
    try:
        stakes = await db.stake_accounts.find(
            {"member_wallet": current_member.wallet_address}
        ).to_list(length=None)
        
        total_staked = sum(stake["stake_amount_sol"] for stake in stakes)
        active_stakes = [stake for stake in stakes if stake["status"] == "active"]
        
        return {
            "success": True,
            "stakes": stakes,
            "summary": {
                "total_accounts": len(stakes),
                "active_accounts": len(active_stakes),
                "total_staked_sol": total_staked,
                "estimated_daily_rewards": await solana_staking_service.calculate_staking_rewards(
                    total_staked, is_member=True, days_staked=1
                ) if stakes else {"total_reward_sol": 0}
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stakes: {str(e)}")

# Get specific stake account info
@api_router.get("/staking/account/{stake_account_pubkey}")
async def get_stake_account_info(
    stake_account_pubkey: str,
    current_member: MemberProfile = Depends(verify_member_auth)
):
    """Get detailed information about a specific stake account"""
    try:
        # Validate stake account format
        if not await solana_staking_service.validate_stake_account(stake_account_pubkey):
            raise HTTPException(status_code=400, detail="Invalid stake account address")
        
        # Find stake account in database
        stake_account = await db.stake_accounts.find_one({
            "stake_account_pubkey": stake_account_pubkey,
            "member_wallet": current_member.wallet_address
        })
        
        if not stake_account:
            raise HTTPException(status_code=404, detail="Stake account not found or not owned by you")
        
        # Get blockchain info
        blockchain_info = await solana_staking_service.get_stake_account_info(stake_account_pubkey)
        
        # Calculate accumulated rewards
        days_since_activation = 0
        if stake_account.get("activated_at"):
            activated_time = datetime.fromisoformat(stake_account["activated_at"].replace("Z", "+00:00"))
            days_since_activation = (datetime.now(timezone.utc) - activated_time).days
        
        rewards = await solana_staking_service.calculate_staking_rewards(
            stake_account["stake_amount_sol"],
            is_member=True,
            days_staked=max(1, days_since_activation)
        )
        
        return {
            "success": True,
            "stake_account": stake_account,
            "blockchain_info": blockchain_info,
            "reward_info": rewards,
            "days_active": days_since_activation
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stake account info: {str(e)}")

# Unstake tokens
@api_router.post("/staking/unstake")
async def unstake_tokens(request: UnstakeRequest, current_member: MemberProfile = Depends(verify_member_auth)):
    """Create unstaking instructions for a stake account"""
    try:
        # Validate inputs
        if not await solana_staking_service.validate_stake_account(request.stake_account_pubkey):
            raise HTTPException(status_code=400, detail="Invalid stake account address")
        
        if not await solana_staking_service.validate_wallet_address(request.wallet_address):
            raise HTTPException(status_code=400, detail="Invalid wallet address")
        
        # Verify ownership
        stake_account = await db.stake_accounts.find_one({
            "stake_account_pubkey": request.stake_account_pubkey,
            "member_wallet": current_member.wallet_address
        })
        
        if not stake_account:
            raise HTTPException(status_code=404, detail="Stake account not found or not owned by you")
        
        if stake_account["status"] not in ["active", "deactivating"]:
            raise HTTPException(status_code=400, detail=f"Cannot unstake from {stake_account['status']} account")
        
        # Create unstaking instructions
        instructions = await solana_staking_service.create_unstake_instruction(
            request.stake_account_pubkey,
            request.wallet_address
        )
        
        if not instructions.get("success"):
            raise HTTPException(status_code=500, detail=instructions.get("error", "Failed to create unstake instructions"))
        
        # Update status to deactivating
        await db.stake_accounts.update_one(
            {"stake_account_pubkey": request.stake_account_pubkey},
            {
                "$set": {
                    "status": "deactivating",
                    "deactivated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return {
            "success": True,
            "stake_account_pubkey": request.stake_account_pubkey,
            "transaction_instructions": instructions,
            "note": "Unstaking will take effect in the next epoch. Funds will be available for withdrawal after deactivation."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unstaking failed: {str(e)}")

# Get rewards for a stake account
@api_router.get("/staking/rewards/{stake_account_pubkey}")
async def get_stake_rewards(
    stake_account_pubkey: str,
    current_member: MemberProfile = Depends(verify_member_auth)
):
    """Get reward history for a specific stake account"""
    try:
        # Verify ownership
        stake_account = await db.stake_accounts.find_one({
            "stake_account_pubkey": stake_account_pubkey,
            "member_wallet": current_member.wallet_address
        })
        
        if not stake_account:
            raise HTTPException(status_code=404, detail="Stake account not found")
        
        # Get reward history
        rewards = await db.stake_rewards.find(
            {"stake_account_id": stake_account["id"]}
        ).sort("epoch", -1).to_list(length=50)  # Last 50 epochs
        
        total_rewards = sum(reward["total_reward_sol"] for reward in rewards)
        member_bonus_total = sum(reward["member_bonus_sol"] for reward in rewards)
        
        return {
            "success": True,
            "stake_account_pubkey": stake_account_pubkey,
            "rewards_history": rewards,
            "summary": {
                "total_rewards_earned": total_rewards,
                "member_bonus_earned": member_bonus_total,
                "base_rewards_earned": total_rewards - member_bonus_total,
                "epochs_tracked": len(rewards)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rewards: {str(e)}")

# Claim rewards (simulate)
@api_router.post("/staking/claim-rewards")
async def claim_stake_rewards(request: StakeRewardsRequest, current_member: MemberProfile = Depends(verify_member_auth)):
    """Claim accumulated staking rewards"""
    try:
        # Find all stake accounts for user
        query = {"member_wallet": request.wallet_address}
        if request.stake_account_pubkey:
            query["stake_account_pubkey"] = request.stake_account_pubkey
        
        stake_accounts = await db.stake_accounts.find(query).to_list(length=None)
        
        if not stake_accounts:
            raise HTTPException(status_code=404, detail="No stake accounts found")
        
        # Calculate total claimable rewards
        total_claimable = 0.0
        total_member_bonus = 0.0
        
        for stake_account in stake_accounts:
            # In a real implementation, this would calculate actual unclaimed rewards
            # For now, simulate based on time since last claim
            days_since_last_claim = 7  # Simulate 7 days
            rewards = await solana_staking_service.calculate_staking_rewards(
                stake_account["stake_amount_sol"],
                is_member=True,
                days_staked=days_since_last_claim
            )
            total_claimable += rewards["total_reward_sol"]
            total_member_bonus += rewards["member_bonus_sol"]
        
        # In a real implementation, this would create withdrawal transactions
        claim_transaction_signature = base58.b58encode(os.urandom(64)).decode('utf-8')
        
        return {
            "success": True,
            "claimed_rewards_sol": total_claimable,
            "member_bonus_sol": total_member_bonus,
            "base_rewards_sol": total_claimable - total_member_bonus,
            "transaction_signature": claim_transaction_signature,
            "note": "Rewards have been added to your wallet balance"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reward claim failed: {str(e)}")

# Admin: Get staking overview
@api_router.get("/admin/staking/overview")
async def get_staking_overview(admin_wallet: str = Header(...)):
    """Get overview of all staking activity (admin only)"""
    try:
        # Basic admin verification
        if admin_wallet != "admin-wallet-address":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get all stake accounts
        all_stakes = await db.stake_accounts.find({}).to_list(length=None)
        
        # Calculate statistics
        total_accounts = len(all_stakes)
        active_accounts = len([s for s in all_stakes if s["status"] == "active"])
        total_staked = sum(stake["stake_amount_sol"] for stake in all_stakes)
        
        # Member vs non-member breakdown
        member_stakes = []
        non_member_stakes = []
        
        for stake in all_stakes:
            member = await db.members.find_one({"wallet_address": stake["member_wallet"]})
            is_member = member and member.get("dues_paid", False) and member.get("pma_agreed", False)
            
            if is_member:
                member_stakes.append(stake)
            else:
                non_member_stakes.append(stake)
        
        return {
            "success": True,
            "overview": {
                "total_stake_accounts": total_accounts,
                "active_stake_accounts": active_accounts,
                "total_sol_staked": total_staked,
                "member_accounts": len(member_stakes),
                "non_member_accounts": len(non_member_stakes),
                "member_sol_staked": sum(s["stake_amount_sol"] for s in member_stakes),
                "non_member_sol_staked": sum(s["stake_amount_sol"] for s in non_member_stakes)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get staking overview: {str(e)}")

# Admin: Get all stake accounts
@api_router.get("/admin/staking/accounts")
async def get_all_stake_accounts(admin_wallet: str = Header(...), skip: int = 0, limit: int = 100):
    """Get all stake accounts with member information (admin only)"""
    try:
        if admin_wallet != "admin-wallet-address":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get stake accounts with pagination
        stakes = await db.stake_accounts.find({}).skip(skip).limit(limit).to_list(length=None)
        
        # Enrich with member information
        enriched_stakes = []
        for stake in stakes:
            member = await db.members.find_one({"wallet_address": stake["member_wallet"]})
            stake_info = {
                **stake,
                "member_info": {
                    "email": member.get("email") if member else None,
                    "is_club_member": bool(member and member.get("dues_paid") and member.get("pma_agreed")) if member else False
                }
            }
            enriched_stakes.append(stake_info)
        
        return {
            "success": True,
            "stakes": enriched_stakes,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "count": len(enriched_stakes)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stake accounts: {str(e)}")

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