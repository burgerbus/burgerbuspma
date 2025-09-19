import React, { useState, useEffect } from 'react';

const SimpleWalletConnect = ({ onWalletConnected, onClose }) => {
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState('');
  const [phantomWallet, setPhantomWallet] = useState(null);

  useEffect(() => {
    // Check if Phantom is installed
    const getProvider = () => {
      if ('solana' in window) {
        const provider = window.solana;
        if (provider.isPhantom) {
          return provider;
        }
      }
      return null;
    };

    const provider = getProvider();
    setPhantomWallet(provider);
  }, []);

  const connectPhantom = async () => {
    if (!phantomWallet) {
      setError('Phantom wallet not detected. Please install Phantom from phantom.app');
      return;
    }

    setIsConnecting(true);
    setError('');

    try {
      const response = await phantomWallet.connect();
      console.log('Phantom connected:', response.publicKey.toString());
      
      // Update member profile with wallet address
      if (onWalletConnected) {
        onWalletConnected(response.publicKey.toString());
      }
      
      if (onClose) {
        onClose();
      }
    } catch (err) {
      console.error('Phantom connection error:', err);
      setError(`Connection failed: ${err.message}`);
    } finally {
      setIsConnecting(false);
    }
  };

  const installPhantom = () => {
    window.open('https://phantom.app/', '_blank');
  };

  return (
    <div className="bg-gray-700 rounded-lg p-4 space-y-4">
      <h3 className="text-white font-bold text-lg">Connect Phantom Wallet</h3>
      
      {error && (
        <div className="bg-red-900/20 border border-red-600 rounded p-3">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {phantomWallet ? (
        <div className="space-y-3">
          <div className="flex items-center text-green-400 text-sm">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
            Phantom wallet detected
          </div>
          
          <button
            onClick={connectPhantom}
            disabled={isConnecting}
            className="w-full py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 text-white font-semibold rounded-lg transition-colors flex items-center justify-center"
          >
            {isConnecting ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Connecting...
              </>
            ) : (
              <>
                <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTA4IiBoZWlnaHQ9IjEwOCIgdmlld0JveD0iMCAwIDEwOCAxMDgiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxnIGNsaXAtcGF0aD0idXJsKCNjbGlwMCkiPgo8cGF0aCBkPSJNODkuNCAzMS43NEg3MC41QzY5LjMyIDI3LjM5IDY1LjI5IDI0IDYwLjQ3IDI0SDE5LjU3QzE0LjIxIDI0IDEyIDI5LjU4IDEyIDM2VjcyQzEyIDc4LjQyIDE0LjIxIDg0IDE5LjU3IDg0SDYwLjQ3QzY1LjI5IDg0IDY5LjMyIDgwLjYxIDcwLjUgNzYuMjZIODkuNEM5NC43NiA3Ni4yNiA5NyA3MC42OCA5NyA2NC4yNlYzMy43NEMxMDcgNDAuNjggOTQuNzYgMzEuNzQgODkuNCAzMS43NFoiIGZpbGw9InVybCgjcGFpbnQwX2xpbmVhcikiLz4KPC9nPgo8ZGVmcz4KPGxpbmVhckdyYWRpZW50IGlkPSJwYWludDBfbGluZWFyIiB4MT0iMTIiIHkxPSI1NCIgeDI9Ijk3IiB5Mj0iNTQiIGdyYWRpZW50VW5pdHM9InVzZXJTcGFjZU9uVXNlIj4KPHN0b3Agc3RvcC1jb2xvcj0iIzVzNCIvPgo8c3RvcCBvZmZzZXQ9IjEiIHN0b3AtY29sb3I9IiM5OTQ1RkYiLz4KPC9saW5lYXJHcmFkaWVudD4KPGNsaXBQYXRoIGlkPSJjbGlwMCI+CjxyZWN0IHdpZHRoPSIxMDgiIGhlaWdodD0iMTA4IiBmaWxsPSJ3aGl0ZSIvPgo8L2NsaXBQYXRoPgo8L2RlZnM+Cjwvc3ZnPg==" alt="Phantom" className="w-5 h-5 mr-2" />
                Connect Phantom
              </>
            )}
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center text-yellow-400 text-sm">
            <div className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></div>
            Phantom wallet not detected
          </div>
          
          <button
            onClick={installPhantom}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
          >
            Install Phantom Wallet
          </button>
          
          <p className="text-gray-400 text-xs text-center">
            After installation, refresh this page and try again
          </p>
        </div>
      )}
    </div>
  );
};

export default SimpleWalletConnect;