use anchor_lang::prelude::*;
use anchor_spl::token::{self, Token, TokenAccount, Transfer, Mint};

declare_id!("BBCStK1ng1111111111111111111111111111111111");

#[program]
pub mod bbc_staking {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        let pool = &mut ctx.accounts.pool;
        pool.authority = ctx.accounts.authority.key();
        pool.total_staked = 0;
        pool.member_count = 0;
        pool.minimum_stake = 1_000_000 * 10_u64.pow(9); // 1M BBC tokens with 9 decimals
        pool.token_mint = ctx.accounts.token_mint.key();
        pool.bump = ctx.bumps.pool;
        
        msg!("BBC Staking Pool initialized with minimum stake: {} tokens", pool.minimum_stake);
        Ok(())
    }

    pub fn stake(ctx: Context<Stake>, amount: u64) -> Result<()> {
        let pool = &mut ctx.accounts.pool;
        let user_account = &mut ctx.accounts.user_account;
        
        require!(amount > 0, StakingError::InvalidAmount);
        require!(amount >= pool.minimum_stake || user_account.amount_staked > 0, StakingError::InsufficientStakeAmount);
        
        // Transfer tokens from user to pool
        let cpi_accounts = Transfer {
            from: ctx.accounts.user_token_account.to_account_info(),
            to: ctx.accounts.pool_token_account.to_account_info(),
            authority: ctx.accounts.user.to_account_info(),
        };
        
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new(cpi_program, cpi_accounts);
        token::transfer(cpi_ctx, amount)?;
        
        // Update user account
        let was_member = user_account.is_member;
        user_account.user = ctx.accounts.user.key();
        user_account.amount_staked += amount;
        user_account.stake_timestamp = Clock::get()?.unix_timestamp;
        user_account.is_member = user_account.amount_staked >= pool.minimum_stake;
        
        // Update pool statistics
        pool.total_staked += amount;
        if user_account.is_member && !was_member {
            pool.member_count += 1;
        }
        
        emit!(StakeEvent {
            user: ctx.accounts.user.key(),
            amount,
            total_staked: user_account.amount_staked,
            is_member: user_account.is_member,
            timestamp: user_account.stake_timestamp,
        });
        
        msg!("User {} staked {} tokens. Total: {}. Member: {}", 
             ctx.accounts.user.key(), 
             amount, 
             user_account.amount_staked, 
             user_account.is_member);
        
        Ok(())
    }

    pub fn unstake(ctx: Context<Unstake>, amount: u64) -> Result<()> {
        let pool = &mut ctx.accounts.pool;
        let user_account = &mut ctx.accounts.user_account;
        
        require!(amount > 0, StakingError::InvalidAmount);
        require!(user_account.amount_staked >= amount, StakingError::InsufficientBalance);
        
        // Check if unstaking would affect membership status
        let new_balance = user_account.amount_staked - amount;
        let was_member = user_account.is_member;
        let will_be_member = new_balance >= pool.minimum_stake;
        
        // Transfer tokens from pool back to user
        let seeds = &[b"pool".as_ref(), &[pool.bump]];
        let signer = &[&seeds[..]];
        
        let cpi_accounts = Transfer {
            from: ctx.accounts.pool_token_account.to_account_info(),
            to: ctx.accounts.user_token_account.to_account_info(),
            authority: pool.to_account_info(),
        };
        
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new_with_signer(cpi_program, cpi_accounts, signer);
        token::transfer(cpi_ctx, amount)?;
        
        // Update user account
        user_account.amount_staked = new_balance;
        user_account.is_member = will_be_member;
        user_account.last_unstake_timestamp = Clock::get()?.unix_timestamp;
        
        // Update pool statistics
        pool.total_staked -= amount;
        if was_member && !will_be_member {
            pool.member_count -= 1;
        }
        
        emit!(UnstakeEvent {
            user: ctx.accounts.user.key(),
            amount,
            remaining_staked: user_account.amount_staked,
            is_member: user_account.is_member,
            timestamp: user_account.last_unstake_timestamp,
        });
        
        msg!("User {} unstaked {} tokens. Remaining: {}. Member: {}", 
             ctx.accounts.user.key(), 
             amount, 
             user_account.amount_staked, 
             user_account.is_member);
        
        Ok(())
    }

    pub fn get_membership_status(ctx: Context<GetMembershipStatus>) -> Result<MembershipStatus> {
        let user_account = &ctx.accounts.user_account;
        let pool = &ctx.accounts.pool;
        
        Ok(MembershipStatus {
            is_member: user_account.is_member,
            amount_staked: user_account.amount_staked,
            stake_timestamp: user_account.stake_timestamp,
            minimum_required: pool.minimum_stake,
            progress_percentage: ((user_account.amount_staked as f64 / pool.minimum_stake as f64) * 100.0) as u8,
        })
    }

    pub fn get_pool_stats(ctx: Context<GetPoolStats>) -> Result<PoolStats> {
        let pool = &ctx.accounts.pool;
        
        Ok(PoolStats {
            total_staked: pool.total_staked,
            member_count: pool.member_count,
            minimum_stake: pool.minimum_stake,
            token_mint: pool.token_mint,
        })
    }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + StakingPool::INIT_SPACE,
        seeds = [b"pool"],
        bump
    )]
    pub pool: Account<'info, StakingPool>,
    
    #[account(mut)]
    pub authority: Signer<'info>,
    
    pub token_mint: Account<'info, Mint>,
    
    #[account(
        init,
        payer = authority,
        token::mint = token_mint,
        token::authority = pool,
        seeds = [b"pool_token_account"],
        bump
    )]
    pub pool_token_account: Account<'info, TokenAccount>,
    
    pub system_program: Program<'info, System>,
    pub token_program: Program<'info, Token>,
    pub rent: Sysvar<'info, Rent>,
}

#[derive(Accounts)]
pub struct Stake<'info> {
    #[account(
        mut,
        seeds = [b"pool"],
        bump = pool.bump
    )]
    pub pool: Account<'info, StakingPool>,
    
    #[account(
        init_if_needed,
        payer = user,
        space = 8 + UserStakeAccount::INIT_SPACE,
        seeds = [b"user", user.key().as_ref()],
        bump
    )]
    pub user_account: Account<'info, UserStakeAccount>,
    
    #[account(mut)]
    pub user: Signer<'info>,
    
    #[account(
        mut,
        constraint = user_token_account.mint == pool.token_mint,
        constraint = user_token_account.owner == user.key()
    )]
    pub user_token_account: Account<'info, TokenAccount>,
    
    #[account(
        mut,
        seeds = [b"pool_token_account"],
        bump
    )]
    pub pool_token_account: Account<'info, TokenAccount>,
    
    pub system_program: Program<'info, System>,
    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct Unstake<'info> {
    #[account(
        mut,
        seeds = [b"pool"],
        bump = pool.bump
    )]
    pub pool: Account<'info, StakingPool>,
    
    #[account(
        mut,
        seeds = [b"user", user.key().as_ref()],
        bump,
        constraint = user_account.user == user.key()
    )]
    pub user_account: Account<'info, UserStakeAccount>,
    
    #[account(mut)]
    pub user: Signer<'info>,
    
    #[account(
        mut,
        constraint = user_token_account.mint == pool.token_mint,
        constraint = user_token_account.owner == user.key()
    )]
    pub user_token_account: Account<'info, TokenAccount>,
    
    #[account(
        mut,
        seeds = [b"pool_token_account"],
        bump
    )]
    pub pool_token_account: Account<'info, TokenAccount>,
    
    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct GetMembershipStatus<'info> {
    #[account(
        seeds = [b"pool"],
        bump = pool.bump
    )]
    pub pool: Account<'info, StakingPool>,
    
    #[account(
        seeds = [b"user", user.key().as_ref()],
        bump
    )]
    pub user_account: Account<'info, UserStakeAccount>,
    
    pub user: Signer<'info>,
}

#[derive(Accounts)]
pub struct GetPoolStats<'info> {
    #[account(
        seeds = [b"pool"],
        bump = pool.bump
    )]
    pub pool: Account<'info, StakingPool>,
}

#[account]
#[derive(InitSpace)]
pub struct StakingPool {
    pub authority: Pubkey,
    pub total_staked: u64,
    pub member_count: u64,
    pub minimum_stake: u64,
    pub token_mint: Pubkey,
    pub bump: u8,
}

#[account]
#[derive(InitSpace)]
pub struct UserStakeAccount {
    pub user: Pubkey,
    pub amount_staked: u64,
    pub stake_timestamp: i64,
    pub last_unstake_timestamp: i64,
    pub is_member: bool,
}

#[derive(AnchorSerialize, AnchorDeserialize)]
pub struct MembershipStatus {
    pub is_member: bool,
    pub amount_staked: u64,
    pub stake_timestamp: i64,
    pub minimum_required: u64,
    pub progress_percentage: u8,
}

#[derive(AnchorSerialize, AnchorDeserialize)]
pub struct PoolStats {
    pub total_staked: u64,
    pub member_count: u64,
    pub minimum_stake: u64,
    pub token_mint: Pubkey,
}

#[event]
pub struct StakeEvent {
    pub user: Pubkey,
    pub amount: u64,
    pub total_staked: u64,
    pub is_member: bool,
    pub timestamp: i64,
}

#[event]
pub struct UnstakeEvent {
    pub user: Pubkey,
    pub amount: u64,
    pub remaining_staked: u64,
    pub is_member: bool,
    pub timestamp: i64,
}

#[error_code]
pub enum StakingError {
    #[msg("Invalid amount: must be greater than 0")]
    InvalidAmount,
    #[msg("Insufficient stake amount for membership: minimum 1,000,000 BBC tokens required")]
    InsufficientStakeAmount,
    #[msg("Insufficient balance for unstaking")]
    InsufficientBalance,
    #[msg("User account not found")]
    UserAccountNotFound,
    #[msg("Unauthorized: only pool authority can perform this action")]
    Unauthorized,
}