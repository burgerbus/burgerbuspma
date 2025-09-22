import React, { useState, useEffect } from 'react';
import SimpleWalletConnect from './SimpleWalletConnect';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const WalletConnectionModal = ({ isOpen, onClose, onWalletConnected }) => {
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);
  const [error, setError] = useState('');
  const [connectedWallet, setConnectedWallet] = useState(null);

  const updateMemberWallet = async (walletAddress) => {
    if (!walletAddress) return;
    
    setIsUpdatingProfile(true);
    setError('');

    try {
      // Update member profile with wallet address
      const response = await bchAuthService.post('/api/profile/update-wallet', {
        wallet_address: walletAddress
      });

      if (response.success) {
        setConnectedWallet(walletAddress);
        onWalletConnected(walletAddress);
        onClose();
      } else {
        setError('Failed to update profile with wallet address');
      }
    } catch (error) {
      console.error('Error updating wallet:', error);
      setError('Failed to connect wallet to your account. Please try again.');
    } finally {
      setIsUpdatingProfile(false);
    }
  };

  const handleWalletConnected = async (walletAddress) => {
    await updateMemberWallet(walletAddress);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div className="bg-gray-800 rounded-lg max-w-md w-full p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white">Connect Solana Wallet</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="space-y-4">
          <p className="text-gray-300 text-sm">
            Connect your Solana wallet to stake BBC tokens and earn rewards. Your wallet will be linked to your member account.
          </p>

          {/* Error Message */}
          {error && (
            <div className="bg-red-900/20 border border-red-600 rounded-lg p-3">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {/* Wallet Connection Status */}
          {connectedWallet ? (
            <div className="bg-green-900/20 border border-green-600 rounded-lg p-4">
              <div className="flex items-center mb-2">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                <span className="text-green-400 font-semibold">Wallet Connected</span>
              </div>
              <div className="text-gray-300 text-sm font-mono break-all">
                {connectedWallet}
              </div>
              
              {isUpdatingProfile && (
                <div className="mt-3 text-yellow-400 text-sm">
                  Updating your member profile...
                </div>
              )}
            </div>
          ) : (
            <SimpleWalletConnect 
              onWalletConnected={handleWalletConnected}
              onClose={onClose}
            />
          )}

          {/* Requirements Info */}
          <div className="bg-blue-900/20 border border-blue-600 rounded-lg p-3">
            <h4 className="text-blue-400 font-semibold text-sm mb-1">For Staking:</h4>
            <p className="text-blue-300 text-xs">
              You'll need 1,000,000 BBC tokens in your wallet to qualify for premium membership and bonus rewards.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WalletConnectionModal;