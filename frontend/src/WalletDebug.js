import React, { useState, useEffect } from 'react';
import BCHWalletManager from './BCHWalletManager';

const WalletDebug = () => {
  const [debugInfo, setDebugInfo] = useState({});
  const [logs, setLogs] = useState([]);
  const [walletManager] = useState(new BCHWalletManager());

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { timestamp, message, type }]);
    console.log(`[${timestamp}] ${message}`);
  };

  useEffect(() => {
    checkWalletEnvironment();
  }, []);

  const checkWalletEnvironment = async () => {
    addLog('🔍 Checking wallet environment...', 'info');
    
    const info = {
      userAgent: navigator.userAgent,
      windowObjects: {},
      detectedWallets: [],
      errors: []
    };

    // Check for various wallet window objects
    const walletChecks = [
      'edgeProvider',
      'edge', 
      'bitcoincom',
      'badger',
      'bitcoincash',
      'bch',
      'ethereum', // Sometimes BCH wallets use this
      'web3'
    ];

    walletChecks.forEach(check => {
      if (window[check]) {
        info.windowObjects[check] = {
          exists: true,
          type: typeof window[check],
          methods: Object.keys(window[check] || {}).slice(0, 10) // First 10 methods
        };
        addLog(`✅ Found window.${check}`, 'success');
      } else {
        info.windowObjects[check] = { exists: false };
        addLog(`❌ No window.${check}`, 'warning');
      }
    });

    // Try to detect wallets
    try {
      const detectedWallets = await walletManager.detectWallets();
      info.detectedWallets = detectedWallets;
      addLog(`🔍 Detected ${detectedWallets.length} wallets: ${detectedWallets.map(w => w.name).join(', ')}`, 'success');
    } catch (error) {
      info.errors.push(`Wallet detection failed: ${error.message}`);
      addLog(`❌ Wallet detection failed: ${error.message}`, 'error');
    }

    setDebugInfo(info);
  };

  const testWalletConnection = async (walletName) => {
    addLog(`🔌 Testing connection to ${walletName}...`, 'info');
    
    try {
      // First detect wallets
      await walletManager.detectWallets();
      
      // Try to connect
      const wallet = await walletManager.connectWallet(walletName);
      addLog(`✅ Successfully connected to ${walletName}!`, 'success');
      addLog(`📍 Address: ${wallet.address}`, 'info');
      
      // Try to sign a test message
      try {
        const testMessage = "Test message for Bitcoin Ben's Burger Bus Club";
        addLog(`✍️ Testing message signing...`, 'info');
        
        const signature = await walletManager.signMessage(testMessage);
        addLog(`✅ Message signed successfully!`, 'success');
        addLog(`📝 Signature: ${signature.signature.slice(0, 50)}...`, 'info');
        
      } catch (signError) {
        addLog(`❌ Message signing failed: ${signError.message}`, 'error');
      }
      
    } catch (error) {
      addLog(`❌ Connection to ${walletName} failed: ${error.message}`, 'error');
      addLog(`🔍 Error details: ${error.stack || error.toString()}`, 'error');
    }
  };

  const clearLogs = () => {
    setLogs([]);
  };

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="bg-gray-800 rounded-lg p-8">
          <h1 className="text-3xl font-bold text-white mb-6">
            🔧 BCH Wallet Connection Debugger
          </h1>
          
          <div className="grid md:grid-cols-2 gap-8">
            {/* Debug Info */}
            <div>
              <h2 className="text-xl font-bold text-white mb-4">🔍 Environment Info</h2>
              
              <div className="bg-gray-700 rounded-lg p-4 mb-4">
                <h3 className="text-white font-medium mb-2">Browser:</h3>
                <code className="text-green-400 text-sm">
                  {debugInfo.userAgent?.slice(0, 100)}...
                </code>
              </div>

              <div className="bg-gray-700 rounded-lg p-4 mb-4">
                <h3 className="text-white font-medium mb-2">Window Objects:</h3>
                <div className="space-y-1 text-sm">
                  {Object.entries(debugInfo.windowObjects || {}).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-gray-300">{key}:</span>
                      <span className={value.exists ? 'text-green-400' : 'text-red-400'}>
                        {value.exists ? '✅ Found' : '❌ Missing'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-gray-700 rounded-lg p-4">
                <h3 className="text-white font-medium mb-2">Detected Wallets:</h3>
                {debugInfo.detectedWallets?.length > 0 ? (
                  <div className="space-y-2">
                    {debugInfo.detectedWallets.map((wallet, index) => (
                      <div key={index} className="bg-gray-600 rounded p-3">
                        <div className="text-white font-medium">{wallet.name}</div>
                        <div className="text-gray-300 text-sm">Type: {wallet.type}</div>
                        <button
                          onClick={() => testWalletConnection(wallet.name)}
                          className="mt-2 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors"
                        >
                          Test Connection
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-red-400">No wallets detected</div>
                )}
              </div>
            </div>

            {/* Logs */}
            <div>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-white">📋 Debug Logs</h2>
                <button
                  onClick={clearLogs}
                  className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white rounded text-sm transition-colors"
                >
                  Clear Logs
                </button>
              </div>
              
              <div className="bg-gray-700 rounded-lg p-4 h-96 overflow-y-auto">
                {logs.length === 0 ? (
                  <div className="text-gray-400">No logs yet...</div>
                ) : (
                  <div className="space-y-2 text-sm font-mono">
                    {logs.map((log, index) => (
                      <div
                        key={index}
                        className={`${
                          log.type === 'error' ? 'text-red-400' :
                          log.type === 'success' ? 'text-green-400' :
                          log.type === 'warning' ? 'text-yellow-400' :
                          'text-gray-300'
                        }`}
                      >
                        <span className="text-gray-500">[{log.timestamp}]</span> {log.message}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="mt-8 flex gap-4">
            <button
              onClick={checkWalletEnvironment}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
            >
              🔄 Refresh Environment Check
            </button>
            
            <button
              onClick={() => testWalletConnection('Demo BCH Wallet')}
              className="px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors"
            >
              🧪 Test Demo Wallet
            </button>
          </div>

          <div className="mt-8 bg-yellow-900/20 border border-yellow-600 rounded-lg p-4">
            <h3 className="text-yellow-400 font-bold mb-2">💡 Troubleshooting Tips:</h3>
            <ul className="text-gray-300 text-sm space-y-1">
              <li>• Make sure Edge Wallet extension is installed and enabled</li>
              <li>• Try refreshing the page after installing Edge Wallet</li>  
              <li>• Check if Edge Wallet is using `window.edgeProvider` or another object name</li>
              <li>• Some wallets require user interaction before they inject into window</li>
              <li>• Edge Wallet might need to be opened/unlocked first</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WalletDebug;