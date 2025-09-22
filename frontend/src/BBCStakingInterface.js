import React, { useState, useEffect } from 'react';
import { useBBCStaking } from './BBCStakingProvider';
import WalletConnectionModal from './WalletConnectionModal';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const BBCStakingInterface = () => {
  const {
    isLoading,
    stakingInfo,
    userStakes,
    totalStaked,
    totalRewards,
    isMember,
    error,
    rewardCalculations,
    MINIMUM_STAKE,
    formatTokenAmount,
    calculateRewards,
    createStake,
    unstakeTokens,
    claimRewards,
    clearError
  } = useBBCStaking();

  const [stakeAmount, setStakeAmount] = useState('');
  const [selectedStake, setSelectedStake] = useState(null);
  const [activeTab, setActiveTab] = useState('stake');
  const [memberInfo, setMemberInfo] = useState(null);
  const [userTokenBalance, setUserTokenBalance] = useState(0);
  const [showWalletModal, setShowWalletModal] = useState(false);
  const [walletConnected, setWalletConnected] = useState(false);

  // Get member info on mount
  useEffect(() => {
    const getMemberInfo = async () => {
      try {
        // Set a timeout to prevent infinite loading
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Request timeout')), 10000)
        );
        
        const profilePromise = bchAuthService.get('/api/profile');
        
        const profile = await Promise.race([profilePromise, timeoutPromise]);
        setMemberInfo(profile);
        
        if (profile?.wallet_address) {
          // Wallet is connected
          setWalletConnected(true);
          
          // Calculate rewards for this wallet
          await calculateRewards(profile.wallet_address);
          
          // Simulate token balance (in real app, this would fetch from blockchain)
          setUserTokenBalance(5000000); // 5M BBC tokens
        } else {
          // No wallet connected
          setWalletConnected(false);
        }
      } catch (error) {
        console.error('Failed to get member info:', error);
        // Set empty member info to stop loading
        setMemberInfo({});
        setWalletConnected(false);
      }
    };

    getMemberInfo();
  }, [calculateRewards]);

  // Handle stake form submission
  const handleStake = async (e) => {
    e.preventDefault();
    
    if (!memberInfo?.wallet_address) {
      alert('Please connect your wallet first');
      return;
    }

    const amountToStake = parseFloat(stakeAmount);
    
    if (!amountToStake || amountToStake < MINIMUM_STAKE) {
      alert(`Minimum stake amount is ${formatTokenAmount(MINIMUM_STAKE)} BBC tokens`);
      return;
    }

    if (amountToStake > userTokenBalance) {
      alert('Insufficient token balance');
      return;
    }

    try {
      // In a real implementation, this would be a proper wallet signature
      const mockSignature = `stake_${Date.now()}_${Math.random().toString(36).substring(7)}`;
      
      const result = await createStake(memberInfo.wallet_address, amountToStake, mockSignature);
      
      alert(`Stake created successfully!\nStake Account: ${result.stake_account.stake_account_pubkey}`);
      setStakeAmount('');
      
    } catch (error) {
      alert(`Staking failed: ${error.message}`);
    }
  };

  // Handle unstake
  const handleUnstake = async (stake) => {
    if (!memberInfo?.wallet_address) {
      alert('Please connect your wallet first');
      return;
    }

    if (window.confirm(`Are you sure you want to unstake ${formatTokenAmount(stake.stake_amount_sol * 1000000)} BBC tokens?`)) {
      try {
        const mockSignature = `unstake_${Date.now()}_${Math.random().toString(36).substring(7)}`;
        
        await unstakeTokens(stake.stake_account_pubkey, memberInfo.wallet_address, mockSignature);
        
        alert('Unstaking initiated successfully! Your tokens will be available after deactivation.');
        
      } catch (error) {
        alert(`Unstaking failed: ${error.message}`);
      }
    }
  };

  // Handle claim rewards
  const handleClaimRewards = async () => {
    if (!memberInfo?.wallet_address) {
      alert('Please connect your wallet first');
      return;
    }

    try {
      const result = await claimRewards(memberInfo.wallet_address);
      
      alert(`Rewards claimed successfully!\nAmount: ${result.claimed_rewards_sol} BBC\nMember Bonus: ${result.member_bonus_sol} BBC`);
      
    } catch (error) {
      alert(`Claiming rewards failed: ${error.message}`);
    }
  };

  // Quick stake amount buttons
  const handleQuickStake = (percentage) => {
    const amount = Math.floor(userTokenBalance * percentage / 100);
    setStakeAmount(amount.toString());
  };

  if (!memberInfo) {
    return (
      <div className="staking-interface p-8 text-center">
        <div className="bg-gray-800 rounded-lg p-8">
          <h2 className="text-2xl font-bold text-white mb-4">BBC Token Staking</h2>
          <p className="text-gray-400 mb-6">Loading staking interface...</p>
          <div className="text-orange-400">
            <svg className="animate-spin h-8 w-8 mx-auto" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
        </div>
      </div>
    );
  }

  // If memberInfo is empty object (API call failed), show authentication required
  if (memberInfo && Object.keys(memberInfo).length === 0) {
    return (
      <div className="staking-interface p-8 text-center">
        <div className="bg-gray-800 rounded-lg p-8">
          <h2 className="text-2xl font-bold text-white mb-4">Authentication Required</h2>
          <p className="text-gray-400 mb-6">Please log in to your member account to access BBC Token staking</p>
          <div className="space-y-4">
            <button
              onClick={() => window.location.href = '/'}
              className="px-6 py-3 bg-orange-600 hover:bg-orange-700 text-white font-semibold rounded-lg transition-colors"
            >
              Go to Login
            </button>
            <p className="text-gray-500 text-sm">
              Need an account? Join the club for FREE membership!
            </p>
          </div>
        </div>
      </div>
    );
  }

  const handleWalletConnected = async (walletAddress) => {
    // Update member info with new wallet address
    setMemberInfo(prev => ({
      ...prev,
      wallet_address: walletAddress
    }));
    setWalletConnected(true);
    
    // Calculate rewards for the connected wallet
    try {
      await calculateRewards(walletAddress);
      // Simulate token balance
      setUserTokenBalance(5000000); // 5M BBC tokens
    } catch (error) {
      console.error('Error calculating rewards for connected wallet:', error);
    }
  };

  return (
    <div className="staking-interface max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-white mb-2">BBC Token Staking</h1>
        <p className="text-gray-400 text-lg">
          Stake {formatTokenAmount(MINIMUM_STAKE)} BBC tokens to qualify for membership
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-900/20 border border-red-600 rounded-lg p-4 flex items-center justify-between">
          <span className="text-red-400">{error}</span>
          <button 
            onClick={clearError}
            className="text-red-400 hover:text-red-300"
          >
            ✕
          </button>
        </div>
      )}

      {/* Staking Info & Member Status */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Member Status */}
        <div className={`rounded-lg p-6 ${isMember ? 'bg-gradient-to-br from-green-900/50 to-green-800/50 border-green-600' : 'bg-gradient-to-br from-gray-800 to-gray-900 border-gray-600'} border`}>
          <h3 className="text-xl font-bold text-white mb-4">Membership Status</h3>
          <div className="flex items-center mb-4">
            <div className={`w-4 h-4 rounded-full mr-3 ${isMember ? 'bg-green-500' : 'bg-gray-500'}`}></div>
            <span className="text-lg font-semibold text-white">
              {isMember ? '🍔 Premium Member' : '👤 Basic User'}
            </span>
          </div>
          
          {/* Wallet Connection Status */}
          <div className="mt-4 pt-4 border-t border-gray-600">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className={`w-3 h-3 rounded-full mr-2 ${walletConnected ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
                <span className="text-sm text-gray-300">
                  {walletConnected ? 'Wallet Connected' : 'Wallet Not Connected'}
                </span>
              </div>
              {!walletConnected && (
                <button
                  onClick={() => setShowWalletModal(true)}
                  className="px-3 py-1 bg-orange-600 hover:bg-orange-700 text-white text-sm rounded transition-colors"
                >
                  Connect Wallet
                </button>
              )}
            </div>
            
            {walletConnected && memberInfo?.wallet_address && (
              <div className="mt-2 text-xs text-gray-400 font-mono break-all">
                {memberInfo.wallet_address}
              </div>
            )}
          </div>
          
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Required Stake:</span>
              <span className="text-white">{formatTokenAmount(MINIMUM_STAKE)} BBC</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Your Balance:</span>
              <span className="text-white">{formatTokenAmount(userTokenBalance)} BBC</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Currently Staked:</span>
              <span className="text-white">{formatTokenAmount(totalStaked * 1000000)} BBC</span>
            </div>
          </div>
          
          {totalStaked * 1000000 >= MINIMUM_STAKE && (
            <div className="mt-4 p-3 bg-green-900/30 rounded-lg">
              <p className="text-green-400 text-sm">
                ✅ Membership requirement met! You're earning bonus rewards.
              </p>
            </div>
          )}
        </div>

        {/* Staking Benefits */}
        <div className="bg-gradient-to-br from-orange-900/50 to-yellow-900/50 border border-orange-600 rounded-lg p-6">
          <h3 className="text-xl font-bold text-white mb-4">Staking Benefits</h3>
          <div className="space-y-3">
            {stakingInfo && (
              <>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Base APY:</span>
                  <span className="text-white font-semibold">{stakingInfo.base_apy}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Member Bonus:</span>
                  <span className="text-green-400 font-semibold">+{stakingInfo.member_bonus_apy}%</span>
                </div>
                <div className="border-t border-orange-600 pt-2">
                  <div className="flex justify-between items-center">
                    <span className="text-orange-400 font-semibold">Total Member APY:</span>
                    <span className="text-orange-400 font-bold text-lg">{stakingInfo.total_member_apy}%</span>
                  </div>
                </div>
              </>
            )}
          </div>
          
          <div className="mt-4 p-3 bg-orange-900/30 rounded-lg">
            <p className="text-orange-300 text-sm">
              🎁 Club members earn bonus rewards on all staking activities!
            </p>
          </div>
        </div>
      </div>

      {/* Reward Projections */}
      {rewardCalculations && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-xl font-bold text-white mb-4">Reward Projections</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(rewardCalculations).map(([period, rewards]) => (
              <div key={period} className="bg-gray-700 rounded-lg p-4 text-center">
                <div className="text-gray-400 text-sm mb-1">
                  {period.replace('_', ' ').toUpperCase()}
                </div>
                <div className="text-white font-bold">
                  {formatTokenAmount(Math.floor(rewards.total_reward_sol * 1000000))} BBC
                </div>
                {rewards.member_bonus_sol > 0 && (
                  <div className="text-green-400 text-xs">
                    +{formatTokenAmount(Math.floor(rewards.member_bonus_sol * 1000000))} bonus
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Staking Actions */}
      <div className="bg-gray-800 rounded-lg overflow-hidden">
        {/* Tabs */}
        <div className="flex border-b border-gray-700">
          <button
            onClick={() => setActiveTab('stake')}
            className={`flex-1 py-4 px-6 font-semibold transition-colors ${
              activeTab === 'stake' 
                ? 'bg-orange-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Stake Tokens
          </button>
          <button
            onClick={() => setActiveTab('manage')}
            className={`flex-1 py-4 px-6 font-semibold transition-colors ${
              activeTab === 'manage' 
                ? 'bg-orange-600 text-white' 
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Manage Stakes ({userStakes.length})
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'stake' && (
            <div>
              <h3 className="text-xl font-bold text-white mb-4">Stake BBC Tokens</h3>
              
              <form onSubmit={handleStake} className="space-y-4">
                <div>
                  <label className="block text-gray-400 text-sm font-medium mb-2">
                    Amount to Stake (BBC Tokens)
                  </label>
                  <input
                    type="number"
                    value={stakeAmount}
                    onChange={(e) => setStakeAmount(e.target.value)}
                    placeholder={`Minimum: ${formatTokenAmount(MINIMUM_STAKE)}`}
                    className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-orange-500 focus:outline-none"
                    disabled={isLoading}
                    min={MINIMUM_STAKE}
                    step="1"
                  />
                  
                  {/* Quick Amount Buttons */}
                  <div className="flex gap-2 mt-2">
                    <button
                      type="button"
                      onClick={() => handleQuickStake(25)}
                      className="px-3 py-1 bg-gray-600 hover:bg-gray-500 text-white text-sm rounded transition-colors"
                    >
                      25%
                    </button>
                    <button
                      type="button"
                      onClick={() => handleQuickStake(50)}
                      className="px-3 py-1 bg-gray-600 hover:bg-gray-500 text-white text-sm rounded transition-colors"
                    >
                      50%
                    </button>
                    <button
                      type="button"
                      onClick={() => handleQuickStake(75)}
                      className="px-3 py-1 bg-gray-600 hover:bg-gray-500 text-white text-sm rounded transition-colors"
                    >
                      75%
                    </button>
                    <button
                      type="button"
                      onClick={() => setStakeAmount(MINIMUM_STAKE.toString())}
                      className="px-3 py-1 bg-orange-600 hover:bg-orange-500 text-white text-sm rounded transition-colors"
                    >
                      Min Required
                    </button>
                  </div>
                </div>

                {!walletConnected ? (
                  <button
                    type="button"
                    onClick={() => setShowWalletModal(true)}
                    className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold rounded-lg transition-all transform hover:scale-105"
                  >
                    Connect Wallet to Stake
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={isLoading || !stakeAmount || parseFloat(stakeAmount) < MINIMUM_STAKE}
                    className="w-full py-4 bg-gradient-to-r from-orange-600 to-yellow-600 hover:from-orange-700 hover:to-yellow-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-bold rounded-lg transition-all transform hover:scale-105 disabled:scale-100 disabled:cursor-not-allowed"
                  >
                    {isLoading ? 'Processing...' : 'Stake BBC Tokens'}
                  </button>
                )}
              </form>
            </div>
          )}

          {activeTab === 'manage' && (
            <div>
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-white">Your Stakes</h3>
                {userStakes.length > 0 && (
                  <button
                    onClick={handleClaimRewards}
                    disabled={isLoading}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white font-semibold rounded-lg transition-colors"
                  >
                    Claim All Rewards
                  </button>
                )}
              </div>

              {userStakes.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-400 text-lg mb-4">No stakes found</div>
                  <p className="text-gray-500">Start staking to earn rewards and qualify for membership!</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {userStakes.map((stake, index) => (
                    <div
                      key={stake.id || index}
                      className="bg-gray-700 rounded-lg p-4 border border-gray-600"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center">
                          <div className={`w-3 h-3 rounded-full mr-3 ${
                            stake.status === 'active' ? 'bg-green-500' :
                            stake.status === 'pending' ? 'bg-yellow-500' :
                            stake.status === 'deactivating' ? 'bg-orange-500' :
                            'bg-gray-500'
                          }`}></div>
                          <span className="text-white font-semibold">
                            {formatTokenAmount(stake.stake_amount_sol * 1000000)} BBC
                          </span>
                          <span className="text-gray-400 ml-2 text-sm">
                            ({stake.status})
                          </span>
                        </div>
                        
                        {stake.status === 'active' && (
                          <button
                            onClick={() => handleUnstake(stake)}
                            disabled={isLoading}
                            className="px-3 py-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white text-sm rounded transition-colors"
                          >
                            Unstake
                          </button>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-400">Created:</span>
                          <div className="text-white">
                            {new Date(stake.created_at).toLocaleDateString()}
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-400">Rewards Earned:</span>
                          <div className="text-green-400">
                            {formatTokenAmount(stake.total_rewards_earned * 1000000)} BBC
                          </div>
                        </div>
                      </div>
                      
                      <div className="mt-2 text-xs text-gray-500 font-mono">
                        {stake.stake_account_pubkey}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      
      {/* Wallet Connection Modal */}
      <WalletConnectionModal
        isOpen={showWalletModal}
        onClose={() => setShowWalletModal(false)}
        onWalletConnected={handleWalletConnected}
      />
    </div>
  );
};

export default BBCStakingInterface;