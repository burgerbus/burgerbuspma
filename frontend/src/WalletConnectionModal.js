import React, { useState, useEffect } from 'react';
import { bchAuthService } from './BCHAuth';
import SimpleWalletConnect from './SimpleWalletConnect';

const WalletConnectionModal = ({ isOpen, onClose, onWalletConnected }) => {
  const { publicKey, connected, disconnect } = useWallet();
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (connected && publicKey) {
      updateMemberWallet();
    }
  }, [connected, publicKey]);

  const updateMemberWallet = async () => {
    if (!publicKey) return;
    
    setIsUpdatingProfile(true);
    setError('');

    try {
      // Update member profile with wallet address
      const response = await bchAuthService.post('/api/profile/update-wallet', {
        wallet_address: publicKey.toString()
      });

      if (response.success) {
        onWalletConnected(publicKey.toString());
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

  const handleDisconnect = async () => {
    try {
      await disconnect();
      setError('');
    } catch (error) {
      console.error('Error disconnecting wallet:', error);
    }
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
          {connected && publicKey ? (
            <div className="bg-green-900/20 border border-green-600 rounded-lg p-4">
              <div className="flex items-center mb-2">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                <span className="text-green-400 font-semibold">Wallet Connected</span>
              </div>
              <div className="text-gray-300 text-sm font-mono break-all">
                {publicKey.toString()}
              </div>
              
              {isUpdatingProfile && (
                <div className="mt-3 text-yellow-400 text-sm">
                  Updating your member profile...
                </div>
              )}
            </div>
          ) : (
            <div className="bg-gray-700 rounded-lg p-4 text-center">
              <p className="text-gray-400 text-sm mb-4">
                No wallet connected. Click below to connect your Solana wallet.
              </p>
            </div>
          )}

          {/* Wallet Connect Button */}
          <div className="flex justify-center">
            <WalletMultiButton className="!bg-orange-600 hover:!bg-orange-700 !rounded-lg !font-semibold" />
          </div>

          {/* Additional Actions */}
          {connected && (
            <div className="flex gap-3">
              <button
                onClick={handleDisconnect}
                className="flex-1 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
              >
                Disconnect
              </button>
            </div>
          )}

          {/* Supported Wallets Info */}
          <div className="bg-gray-700 rounded-lg p-3">
            <h4 className="text-white font-semibold text-sm mb-2">Supported Wallets:</h4>
            <div className="grid grid-cols-2 gap-2 text-xs text-gray-300">
              <div>• Phantom</div>
              <div>• Solflare</div>
              <div>• Backpack</div>
              <div>• Torus</div>
            </div>
          </div>

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