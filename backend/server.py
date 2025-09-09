from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from fastapi_walletauth import jwt_authorization_router, JWTWalletAuthDep

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Set application name for wallet auth
os.environ["FASTAPI_WALLETAUTH_APP"] = "Bitcoin Ben's Burger Bus Club"

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
    wallet_address: str
    full_name: str = ""
    email: str = ""
    phone: str = ""
    membership_tier: str = "basic"  # basic, premium, vip
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    favorite_items: List[str] = []
    total_orders: int = 0
    pma_agreed: bool = False
    dues_paid: bool = False
    payment_amount: float = 0.0

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

# Include wallet authentication routes in API router
api_router.include_router(jwt_authorization_router, prefix="/auth")

# Authentication dependency
async def get_authenticated_member(wa: JWTWalletAuthDep) -> MemberProfile:
    member = await get_or_create_member(wa.address)
    return member

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
    return {"message": "Profile updated successfully"}
@api_router.post("/membership/register")
async def register_membership(member_data: dict, member: MemberProfile = Depends(get_authenticated_member)):
    """Register new membership with PMA agreement and dues payment"""
    try:
        # Check if member already exists
        existing_member = await db.members.find_one({"wallet_address": wa.address})
        if existing_member:
            # Update existing member with PMA info
            await db.members.update_one(
                {"wallet_address": wa.address},
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
            updated_member = await db.members.find_one({"wallet_address": wa.address})
            return {"message": "Membership updated successfully", "member": MemberProfile(**updated_member)}
        else:
            # Create new member
            new_member = MemberProfile(
                wallet_address=wa.address,
                full_name=member_data.get("fullName", ""),
                email=member_data.get("email", ""),
                phone=member_data.get("phone", ""),
                pma_agreed=member_data.get("pma_agreed", False),
                dues_paid=member_data.get("dues_paid", False),
                payment_amount=member_data.get("payment_amount", 0.0)
            )
            member_dict = new_member.dict()
            # Convert datetime to string for MongoDB storage
            if 'joined_at' in member_dict and isinstance(member_dict['joined_at'], datetime):
                member_dict['joined_at'] = member_dict['joined_at'].isoformat()
            await db.members.insert_one(member_dict)
            return {"message": "Membership created successfully", "member": new_member}
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
    """Create a pre-order for pickup."""
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