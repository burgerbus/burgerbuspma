"""
BBC Token Staking Rewards Treasury Management System

This module handles:
1. Reward pool funding and management
2. Automated reward distribution
3. Treasury balance tracking
4. Yield farming strategies
5. Admin controls for rewards
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Treasury Configuration
TREASURY_WALLET_ADDRESS = os.getenv("TREASURY_WALLET_ADDRESS", "TreasuryWallet1111111111111111111111111111")
REWARDS_TOKEN_MINT = os.getenv("PUMP_FUN_TOKEN_ADDRESS", "mWusXdRfsYAoFtYdaDcf8tmG7hnRNvnVc2TuvNEpump")

# Reward Distribution Settings
BASE_APY = Decimal("0.07")  # 7% base APY
MEMBER_BONUS_APY = Decimal("0.02")  # 2% member bonus
COMPOUND_FREQUENCY = 365  # Daily compounding
MIN_REWARD_CLAIM = Decimal("1000")  # Minimum 1000 BBC tokens to claim

class RewardsTreasury:
    def __init__(self, db_client: AsyncIOMotorClient):
        self.db = db_client.get_database("bbc_staking")
        self.treasury_collection = self.db.treasury
        self.rewards_collection = self.db.reward_distributions
        self.stakes_collection = self.db.stakes
        
    async def initialize_treasury(self, initial_funding: Decimal) -> Dict:
        """Initialize the rewards treasury with initial funding"""
        try:
            treasury_record = {
                "treasury_id": "main_treasury",
                "wallet_address": TREASURY_WALLET_ADDRESS,
                "token_mint": REWARDS_TOKEN_MINT,
                "total_funded": float(initial_funding),
                "total_distributed": 0.0,
                "available_balance": float(initial_funding),
                "reserved_for_rewards": 0.0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "status": "active"
            }
            
            # Upsert treasury record
            await self.treasury_collection.replace_one(
                {"treasury_id": "main_treasury"},
                treasury_record,
                upsert=True
            )
            
            logging.info(f"Treasury initialized with {initial_funding} BBC tokens")
            return {"success": True, "treasury": treasury_record}
            
        except Exception as e:
            logging.error(f"Treasury initialization failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def add_funding(self, amount: Decimal, funding_source: str) -> Dict:
        """Add funding to the rewards treasury"""
        try:
            treasury = await self.treasury_collection.find_one({"treasury_id": "main_treasury"})
            if not treasury:
                return {"success": False, "error": "Treasury not initialized"}
            
            # Update treasury balances
            new_funded = treasury["total_funded"] + float(amount)
            new_available = treasury["available_balance"] + float(amount)
            
            await self.treasury_collection.update_one(
                {"treasury_id": "main_treasury"},
                {
                    "$set": {
                        "total_funded": new_funded,
                        "available_balance": new_available,
                        "last_updated": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            # Record funding transaction
            funding_record = {
                "funding_id": f"funding_{int(datetime.now(timezone.utc).timestamp())}",
                "amount": float(amount),
                "funding_source": funding_source,
                "transaction_type": "funding",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "treasury_balance_after": new_available
            }
            
            await self.rewards_collection.insert_one(funding_record)
            
            logging.info(f"Added {amount} BBC funding from {funding_source}")
            return {"success": True, "funding": funding_record, "new_balance": new_available}
            
        except Exception as e:
            logging.error(f"Funding addition failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def calculate_rewards_owed(self) -> Dict:
        """Calculate total rewards owed to all stakers"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Get all active stakes
            stakes = await self.stakes_collection.find({"status": "active"}).to_list(length=None)
            
            total_rewards_owed = Decimal("0")
            staker_rewards = []
            
            for stake in stakes:
                # Calculate time since last reward distribution
                last_reward_time = datetime.fromisoformat(stake.get("last_reward_time", stake["created_at"]))
                time_diff = current_time - last_reward_time
                days_elapsed = Decimal(str(time_diff.total_seconds() / 86400))  # Convert to days
                
                # Get staker member status for bonus calculation
                stake_amount = Decimal(str(stake["amount_staked"]))
                is_member = stake.get("is_member", False)
                
                # Calculate APY (base + member bonus if applicable)
                total_apy = BASE_APY
                if is_member:
                    total_apy += MEMBER_BONUS_APY
                
                # Calculate rewards using compound interest formula
                # A = P(1 + r/n)^(nt) where:
                # P = principal, r = annual rate, n = compound frequency, t = time in years
                principal = stake_amount
                rate = total_apy
                n = Decimal(str(COMPOUND_FREQUENCY))
                t = days_elapsed / Decimal("365")
                
                # Compound interest calculation
                compound_factor = (1 + rate / n) ** (n * t)
                new_amount = principal * compound_factor
                reward_amount = new_amount - principal
                
                if reward_amount > Decimal("0"):
                    staker_reward = {
                        "stake_id": stake["stake_id"],
                        "staker_wallet": stake["staker_wallet"],
                        "stake_amount": float(stake_amount),
                        "is_member": is_member,
                        "apy_applied": float(total_apy),
                        "days_elapsed": float(days_elapsed),
                        "reward_amount": float(reward_amount),
                        "calculation_time": current_time.isoformat()
                    }
                    
                    staker_rewards.append(staker_reward)
                    total_rewards_owed += reward_amount
            
            return {
                "success": True,
                "total_rewards_owed": float(total_rewards_owed),
                "staker_count": len(staker_rewards),
                "staker_rewards": staker_rewards,
                "calculation_time": current_time.isoformat()
            }
            
        except Exception as e:
            logging.error(f"Reward calculation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def distribute_rewards(self) -> Dict:
        """Distribute rewards to all eligible stakers"""
        try:
            # Calculate rewards owed
            rewards_calculation = await self.calculate_rewards_owed()
            if not rewards_calculation["success"]:
                return rewards_calculation
            
            total_rewards_owed = Decimal(str(rewards_calculation["total_rewards_owed"]))
            staker_rewards = rewards_calculation["staker_rewards"]
            
            # Check treasury balance
            treasury = await self.treasury_collection.find_one({"treasury_id": "main_treasury"})
            if not treasury:
                return {"success": False, "error": "Treasury not found"}
            
            available_balance = Decimal(str(treasury["available_balance"]))
            
            if available_balance < total_rewards_owed:
                return {
                    "success": False, 
                    "error": f"Insufficient treasury balance. Need: {total_rewards_owed}, Have: {available_balance}"
                }
            
            # Distribute rewards
            successful_distributions = []
            failed_distributions = []
            total_distributed = Decimal("0")
            
            for reward in staker_rewards:
                try:
                    reward_amount = Decimal(str(reward["reward_amount"]))
                    
                    # Only distribute if above minimum claim threshold
                    if reward_amount >= MIN_REWARD_CLAIM:
                        # Update stake record with reward
                        await self.stakes_collection.update_one(
                            {"stake_id": reward["stake_id"]},
                            {
                                "$inc": {"total_rewards_earned": float(reward_amount)},
                                "$set": {
                                    "last_reward_time": datetime.now(timezone.utc).isoformat(),
                                    "last_reward_amount": float(reward_amount)
                                }
                            }
                        )
                        
                        # Record distribution
                        distribution_record = {
                            "distribution_id": f"dist_{reward['stake_id']}_{int(datetime.now(timezone.utc).timestamp())}",
                            "stake_id": reward["stake_id"],
                            "staker_wallet": reward["staker_wallet"],
                            "amount": float(reward_amount),
                            "apy_applied": reward["apy_applied"],
                            "is_member_bonus": reward["is_member"],
                            "distribution_time": datetime.now(timezone.utc).isoformat(),
                            "status": "distributed"
                        }
                        
                        await self.rewards_collection.insert_one(distribution_record)
                        successful_distributions.append(distribution_record)
                        total_distributed += reward_amount
                    
                except Exception as e:
                    failed_distributions.append({
                        "stake_id": reward["stake_id"],
                        "error": str(e)
                    })
            
            # Update treasury balance
            new_balance = available_balance - total_distributed
            new_total_distributed = treasury["total_distributed"] + float(total_distributed)
            
            await self.treasury_collection.update_one(
                {"treasury_id": "main_treasury"},
                {
                    "$set": {
                        "available_balance": float(new_balance),
                        "total_distributed": new_total_distributed,
                        "last_updated": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            return {
                "success": True,
                "total_distributed": float(total_distributed),
                "successful_distributions": len(successful_distributions),
                "failed_distributions": len(failed_distributions),
                "remaining_treasury_balance": float(new_balance),
                "distribution_time": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logging.error(f"Reward distribution failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_treasury_status(self) -> Dict:
        """Get current treasury status and metrics"""
        try:
            treasury = await self.treasury_collection.find_one({"treasury_id": "main_treasury"}) 
            if not treasury:
                return {"success": False, "error": "Treasury not initialized"}
            
            # Get recent distribution stats
            recent_distributions = await self.rewards_collection.find(
                {"transaction_type": {"$ne": "funding"}},
                sort=[("distribution_time", -1)]
            ).limit(10).to_list(length=None)
            
            # Calculate metrics
            total_active_stakes = await self.stakes_collection.count_documents({"status": "active"})
            rewards_calculation = await self.calculate_rewards_owed()
            
            status = {
                "treasury": {
                    "wallet_address": treasury["wallet_address"],
                    "total_funded": treasury["total_funded"],
                    "total_distributed": treasury["total_distributed"],
                    "available_balance": treasury["available_balance"],
                    "utilization_rate": (treasury["total_distributed"] / treasury["total_funded"] * 100) if treasury["total_funded"] > 0 else 0
                },
                "staking_metrics": {
                    "total_active_stakes": total_active_stakes,
                    "pending_rewards": rewards_calculation.get("total_rewards_owed", 0) if rewards_calculation["success"] else 0
                },
                "recent_activity": recent_distributions,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            return {"success": True, "status": status}
            
        except Exception as e:
            logging.error(f"Treasury status check failed: {e}")
            return {"success": False, "error": str(e)}

# Treasury Management Functions
async def setup_automated_rewards_distribution():
    """Setup automated daily rewards distribution"""
    # This would be called by a cron job or scheduled task
    pass

async def emergency_treasury_pause():
    """Emergency function to pause all reward distributions"""
    pass

async def calculate_optimal_funding_amount(projected_stakes: float, time_horizon_days: int) -> float:
    """Calculate optimal treasury funding amount based on projections"""
    # Calculate expected rewards for projected stakes over time horizon
    base_rewards = projected_stakes * float(BASE_APY) * (time_horizon_days / 365)
    member_rewards = projected_stakes * 0.5 * float(MEMBER_BONUS_APY) * (time_horizon_days / 365)  # Assume 50% are members
    
    total_expected_rewards = base_rewards + member_rewards
    
    # Add 20% buffer for safety
    recommended_funding = total_expected_rewards * 1.2
    
    return recommended_funding