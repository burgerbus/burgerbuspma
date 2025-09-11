import React, { useState, useEffect, useCallback } from 'react';
import BCHWalletManager from './BCHWalletManager';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// BCH Auth Service
class BCHAuthService {
  constructor() {
    this.apiClient = axios.create({
      baseURL: BACKEND_URL,
      headers: { 'Content-Type': 'application/json' }
    });

    this.apiClient.interceptors.request.use((config) => {
      const token = this.getStoredToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  async requestChallenge(appName = 'Bitcoin Ben\'s Burger Bus Club') {
    const response = await this.apiClient.post('/api/auth/challenge', {
      app_name: appName
    });
    return response.data;
  }

  async verifySignature(challengeId, bchAddress, signature, message) {
    const response = await this.apiClient.post('/api/auth/verify', {
      challenge_id: challengeId,
      bch_address: bchAddress,
      signature: signature,
      message: message
    });
    
    this.storeToken(response.data.access_token);
    return response.data;
  }

  async logout() {
    try {
      // No specific logout endpoint needed for JWT
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      this.clearToken();
    }
  }

  storeToken(token) {
    localStorage.setItem('bch_auth_token', token);
  }

  getStoredToken() {
    return localStorage.getItem('bch_auth_token');
  }

  clearToken() {
    localStorage.removeItem('bch_auth_token');
  }

  isAuthenticated() {
    const token = this.getStoredToken();
    if (!token) return false;

    try {
      // Check if token is expired
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      return payload.exp > currentTime;
    } catch (error) {
      return false;
    }
  }

  async get(endpoint) {
    const response = await this.apiClient.get(endpoint);
    return response.data;
  }

  async post(endpoint, data) {
    const response = await this.apiClient.post(endpoint, data);
    return response.data;
  }
}

const bchAuthService = new BCHAuthService();

// Wallet Selection Component
export const BCHWalletSelector = ({ onWalletSelected }) => {
  const [availableWallets, setAvailableWallets] = useState([]);
  const [isDetecting, setIsDetecting] = useState(true);
  const walletManager = new BCHWalletManager();

  useEffect(() => {
    const detectWallets = async () => {
      try {
        const wallets = await walletManager.detectWallets();
        setAvailableWallets(wallets);
      } catch (error) {
        console.error('Wallet detection failed:', error);
      } finally {
        setIsDetecting(false);
      }
    };

    detectWallets();
  }, []);

  if (isDetecting) {
    return (
      <div className="wallet-selector loading">
        <div className="flex items-center justify-center mb-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
        </div>
        <p className="text-gray-400 text-center">Detecting Bitcoin Cash wallets...</p>
      </div>
    );
  }

  return (
    <div className="wallet-selector">
      <h3 className="text-xl font-bold text-white mb-6 text-center">Select Your Bitcoin Cash Wallet</h3>
      <div className="space-y-4">
        {availableWallets.map((wallet) => (
          <button
            key={wallet.name}
            className="w-full bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-lg p-4 text-left transition-colors"
            onClick={() => onWalletSelected(wallet.name)}
          >
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-orange-600 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-lg">₿</span>
              </div>
              <div>
                <h4 className="text-white font-medium">{wallet.name}</h4>
                <p className="text-gray-400 text-sm">
                  {wallet.type === 'extension' ? 'Browser Extension' : 
                   wallet.type === 'mobile' ? 'Mobile Wallet' : 'Demo Wallet (Testing)'}
                </p>
              </div>
            </div>
          </button>
        ))}
      </div>
      
      {availableWallets.length === 0 && (
        <div className="text-center text-gray-400 py-8">
          <p className="mb-4">No Bitcoin Cash wallets found.</p>
          <div className="text-sm space-y-2">
            <p>Recommended wallets:</p>
            <ul className="space-y-1">
              <li>• <a href="https://badger.bitcoin.com/" target="_blank" rel="noopener noreferrer" className="text-orange-400 hover:underline">Badger Wallet</a> (Browser Extension)</li>
              <li>• <a href="https://wallet.bitcoin.com/" target="_blank" rel="noopener noreferrer" className="text-orange-400 hover:underline">Bitcoin.com Wallet</a> (Mobile)</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

// Main BCH Authentication Component
export const BCHAuthentication = ({ onAuthSuccess, onAuthError }) => {
  const [authState, setAuthState] = useState('idle'); // idle, selecting, connecting, signing, verifying
  const [error, setError] = useState(null);
  const [walletManager] = useState(new BCHWalletManager());

  const handleWalletSelected = async (walletName) => {
    setError(null);
    setAuthState('connecting');

    try {
      console.log(`🔄 Attempting to connect to ${walletName}...`);
      
      // Step 1: Detect wallets first to populate availableWallets array
      console.log('🔍 Detecting available wallets...');
      const detectedWallets = await walletManager.detectWallets();
      console.log('✅ Detected wallets:', detectedWallets.map(w => w.name));
      
      // Step 2: Connect to wallet
      setAuthState('connecting');
      console.log(`🔌 Connecting to ${walletName}...`);
      const wallet = await walletManager.connectWallet(walletName);
      console.log('✅ Wallet connected:', wallet);
      
      // Step 3: Generate authentication challenge
      setAuthState('challenge');
      console.log('🎯 Requesting authentication challenge...');
      const challengeResponse = await bchAuthService.requestChallenge();
      console.log('✅ Challenge received:', challengeResponse);
      
      // Step 4: Sign challenge message
      setAuthState('signing');
      console.log('✍️ Signing challenge message...');
      const signatureData = await walletManager.signMessage(challengeResponse.message);
      console.log('✅ Message signed:', signatureData);
      
      // Step 5: Verify signature and get token
      setAuthState('verifying');
      console.log('🔐 Verifying signature...');
      const tokenData = await bchAuthService.verifySignature(
        challengeResponse.challenge_id,
        signatureData.address,
        signatureData.signature,
        signatureData.message
      );
      
      console.log('🎉 Authentication successful:', tokenData);
      setAuthState('success');
      onAuthSuccess && onAuthSuccess(signatureData.address);

    } catch (error) {
      console.error('❌ Authentication failed:', error);
      console.error('Error details:', error.stack);
      
      let errorMessage = error.message || 'Authentication failed';
      
      // Provide more specific error messages
      if (error.message.includes('not available')) {
        errorMessage = `${walletName} is not installed or not available. Please install the wallet extension and try again.`;
      } else if (error.message.includes('denied')) {
        errorMessage = 'Wallet connection was denied. Please approve the connection request in your wallet.';
      } else if (error.message.includes('signing failed')) {
        errorMessage = 'Message signing failed. Please approve the signing request in your wallet.';
      }
      
      setError(errorMessage);
      setAuthState('error');
      onAuthError && onAuthError(error);
    }
  };

  const resetAuth = () => {
    setError(null);
    setAuthState('idle');
  };

  const handleLogout = useCallback(async () => {
    await bchAuthService.logout();
    walletManager.disconnect();
    window.location.reload();
  }, [walletManager]);

  if (bchAuthService.isAuthenticated()) {
    const token = bchAuthService.getStoredToken();
    let address = 'Unknown';
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      address = payload.sub;
    } catch (e) {
      console.error('Token decode error:', e);
    }

    return (
      <div className="flex items-center gap-4">
        <span className="text-green-400 text-sm">✓ Connected: {address.slice(0, 20)}...</span>
        <button
          onClick={handleLogout}
          className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm transition-colors"
        >
          Logout
        </button>
      </div>
    );
  }

  return (
    <div className="bch-authentication">
      {authState === 'idle' && (
        <div className="auth-start text-center">
          <h2 className="text-2xl font-bold text-white mb-4">Sign In with Bitcoin Cash</h2>
          <p className="text-gray-400 mb-6">Connect your Bitcoin Cash wallet to authenticate securely without passwords.</p>
          <button 
            className="px-8 py-3 bg-orange-600 hover:bg-orange-700 text-white rounded-lg font-medium transition-colors"
            onClick={() => setAuthState('selecting')}
          >
            Connect BCH Wallet
          </button>
        </div>
      )}

      {authState === 'selecting' && (
        <BCHWalletSelector onWalletSelected={handleWalletSelected} />
      )}

      {authState === 'connecting' && (
        <div className="auth-progress text-center">
          <div className="flex justify-center mb-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
          </div>
          <h3 className="text-xl font-bold text-white mb-2">Connecting to Wallet</h3>
          <p className="text-gray-400">Please check your wallet for connection approval.</p>
        </div>
      )}

      {authState === 'challenge' && (
        <div className="auth-progress text-center">
          <div className="flex justify-center mb-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
          </div>
          <h3 className="text-xl font-bold text-white mb-2">Generating Challenge</h3>
          <p className="text-gray-400">Creating authentication challenge...</p>
        </div>
      )}

      {authState === 'signing' && (
        <div className="auth-progress text-center">
          <div className="flex justify-center mb-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
          </div>
          <h3 className="text-xl font-bold text-white mb-2">Waiting for Signature</h3>
          <p className="text-gray-400">Please sign the authentication message in your wallet.</p>
        </div>
      )}

      {authState === 'verifying' && (
        <div className="auth-progress text-center">
          <div className="flex justify-center mb-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
          </div>
          <h3 className="text-xl font-bold text-white mb-2">Verifying Signature</h3>
          <p className="text-gray-400">Confirming your identity...</p>
        </div>
      )}

      {authState === 'success' && (
        <div className="auth-success text-center">
          <div className="text-green-400 text-4xl mb-4">✅</div>
          <h3 className="text-xl font-bold text-white mb-2">Authentication Successful</h3>
          <p className="text-gray-400">Welcome to Bitcoin Ben's Burger Bus Club!</p>
        </div>
      )}

      {authState === 'error' && (
        <div className="auth-error text-center">
          <div className="text-red-400 text-4xl mb-4">❌</div>
          <h3 className="text-xl font-bold text-white mb-2">Authentication Failed</h3>
          <p className="text-red-400 mb-4">{error}</p>
          <button 
            onClick={resetAuth}
            className="px-6 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-colors"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
};

export { bchAuthService };