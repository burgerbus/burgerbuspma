import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

const BBCStakingContext = createContext();

export const useBBCStaking = () => {
  const context = useContext(BBCStakingContext);
  if (!context) {
    throw new Error('useBBCStaking must be used within a BBCStakingProvider');
  }
  return context;
};

export const BBCStakingProvider = ({ children }) => {
  const [stakingState, setStakingState] = useState({
    isLoading: false,
    stakingInfo: null,
    userStakes: [],
    totalStaked: 0,
    totalRewards: 0,
    isMember: false,
    error: null,
    rewardCalculations: null
  });

  // Configuration
  const BBC_TOKEN_MINT = process.env.REACT_APP_BBC_TOKEN_MINT || "mWusXdRfsYAoFtYdaDcf8tmG7hnRNvnVc2TuvNEpump";
  const MINIMUM_STAKE = 1000000; // 1M BBC tokens
  const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  // Fetch staking information
  const fetchStakingInfo = useCallback(async () => {
    try {
      setStakingState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const response = await fetch(`${API_BASE_URL}/api/staking/info`);
      if (!response.ok) {
        throw new Error('Failed to fetch staking info');
      }
      
      const data = await response.json();
      
      setStakingState(prev => ({
        ...prev,
        stakingInfo: data.staking_info,
        isLoading: false
      }));
      
      return data.staking_info;
    } catch (error) {
      console.error('Error fetching staking info:', error);
      setStakingState(prev => ({
        ...prev,
        error: error.message,
        isLoading: false
      }));
      throw error;
    }
  }, [API_BASE_URL]);

  // Calculate potential rewards
  const calculateRewards = useCallback(async (walletAddress) => {
    try {
      setStakingState(prev => ({ ...prev, isLoading: true }));
      
      const response = await fetch(`${API_BASE_URL}/api/staking/calculate-rewards`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          wallet_address: walletAddress
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to calculate rewards');
      }
      
      const data = await response.json();
      
      setStakingState(prev => ({
        ...prev,
        rewardCalculations: data.reward_calculations,
        isMember: data.is_club_member,
        isLoading: false
      }));
      
      return data;
    } catch (error) {
      console.error('Error calculating rewards:', error);
      setStakingState(prev => ({
        ...prev,
        error: error.message,
        isLoading: false
      }));
      throw error;
    }
  }, [API_BASE_URL]);

  // Create stake
  const createStake = useCallback(async (walletAddress, amountBBC, signature) => {
    try {
      setStakingState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const response = await fetch(`${API_BASE_URL}/api/staking/create-stake`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        },
        body: JSON.stringify({
          wallet_address: walletAddress,
          amount_sol: amountBBC / 1000000, // Convert BBC to "SOL" equivalent for demo
          wallet_signature: signature
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create stake');
      }
      
      const data = await response.json();
      
      // Refresh user stakes after creating
      await fetchUserStakes();
      
      setStakingState(prev => ({ ...prev, isLoading: false }));
      
      return data;
    } catch (error) {
      console.error('Error creating stake:', error);
      setStakingState(prev => ({
        ...prev,
        error: error.message,
        isLoading: false
      }));
      throw error;
    }
  }, [API_BASE_URL]);

  // Fetch user stakes
  const fetchUserStakes = useCallback(async () => {
    try {
      const token = localStorage.getItem('accessToken');
      if (!token) return;

      const response = await fetch(`${API_BASE_URL}/api/staking/my-stakes`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('accessToken');
          return;
        }
        throw new Error('Failed to fetch user stakes');
      }
      
      const data = await response.json();
      
      setStakingState(prev => ({
        ...prev,
        userStakes: data.stakes || [],
        totalStaked: data.summary?.total_staked_sol || 0,
        totalRewards: data.summary?.estimated_daily_rewards?.total_reward_sol || 0
      }));
      
      return data;
    } catch (error) {
      console.error('Error fetching user stakes:', error);
      setStakingState(prev => ({
        ...prev,
        error: error.message
      }));
    }
  }, [API_BASE_URL]);

  // Unstake tokens
  const unstakeTokens = useCallback(async (stakeAccountPubkey, walletAddress, signature) => {
    try {
      setStakingState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const response = await fetch(`${API_BASE_URL}/api/staking/unstake`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        },
        body: JSON.stringify({
          stake_account_pubkey: stakeAccountPubkey,
          wallet_address: walletAddress,
          wallet_signature: signature
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to unstake');
      }
      
      const data = await response.json();
      
      // Refresh user stakes after unstaking
      await fetchUserStakes();
      
      setStakingState(prev => ({ ...prev, isLoading: false }));
      
      return data;
    } catch (error) {
      console.error('Error unstaking:', error);
      setStakingState(prev => ({
        ...prev,
        error: error.message,
        isLoading: false
      }));
      throw error;
    }
  }, [API_BASE_URL, fetchUserStakes]);

  // Claim rewards
  const claimRewards = useCallback(async (walletAddress, stakeAccountPubkey = null) => {
    try {
      setStakingState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const response = await fetch(`${API_BASE_URL}/api/staking/claim-rewards`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        },
        body: JSON.stringify({
          wallet_address: walletAddress,
          stake_account_pubkey: stakeAccountPubkey
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to claim rewards');
      }
      
      const data = await response.json();
      
      // Refresh user stakes after claiming
      await fetchUserStakes();
      
      setStakingState(prev => ({ ...prev, isLoading: false }));
      
      return data;
    } catch (error) {
      console.error('Error claiming rewards:', error);
      setStakingState(prev => ({
        ...prev,
        error: error.message,
        isLoading: false
      }));
      throw error;
    }
  }, [API_BASE_URL, fetchUserStakes]);

  // Initialize staking info on mount
  useEffect(() => {
    fetchStakingInfo();
  }, [fetchStakingInfo]);

  // Fetch user stakes if authenticated
  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      fetchUserStakes();
    }
  }, [fetchUserStakes]);

  const value = {
    ...stakingState,
    BBC_TOKEN_MINT,
    MINIMUM_STAKE,
    
    // Actions
    fetchStakingInfo,
    calculateRewards,
    createStake,
    fetchUserStakes,
    unstakeTokens,
    claimRewards,
    
    // Utilities
    formatTokenAmount: (amount) => {
      if (amount >= 1000000) {
        return `${(amount / 1000000).toFixed(1)}M`;
      } else if (amount >= 1000) {
        return `${(amount / 1000).toFixed(1)}K`;
      }
      return amount.toLocaleString();
    },
    
    clearError: () => setStakingState(prev => ({ ...prev, error: null }))
  };

  return (
    <BBCStakingContext.Provider value={value}>
      {children}
    </BBCStakingContext.Provider>
  );
};