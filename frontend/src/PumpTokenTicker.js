import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const PumpTokenTicker = () => {
  const [tokenData, setTokenData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTokenData = async () => {
      try {
        setLoading(true);
        const [tokenInfoResponse, tokenPriceResponse] = await Promise.all([
          fetch(`${BACKEND_URL}/api/pump/token-info`),
          fetch(`${BACKEND_URL}/api/pump/token-price`)
        ]);
        
        const tokenInfo = await tokenInfoResponse.json();
        const tokenPrice = await tokenPriceResponse.json();
        
        setTokenData({
          ...tokenInfo.token,
          ...tokenPrice
        });
      } catch (err) {
        console.error('Error fetching token data:', err);
        setError('Failed to load token data');
      } finally {
        setLoading(false);
      }
    };

    fetchTokenData();
    
    // Update every 30 seconds
    const interval = setInterval(fetchTokenData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="bg-gradient-to-r from-yellow-600 to-orange-600 text-white px-4 py-2 text-center">
        <div className="max-w-7xl mx-auto">
          <span className="animate-pulse">Loading token data...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gradient-to-r from-red-600 to-red-700 text-white px-4 py-2 text-center">
        <div className="max-w-7xl mx-auto">
          <span>⚠️ {error}</span>
        </div>
      </div>
    );
  }

  if (!tokenData) return null;

  const formatPrice = (price) => {
    if (price < 0.01) {
      return `$${price.toFixed(6)}`;
    }
    return `$${price.toFixed(4)}`;
  };

  const formatLargeNumber = (num) => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toLocaleString();
  };

  return (
    <div className="bg-gradient-to-r from-yellow-600 to-orange-600 text-white px-4 py-2 text-center relative overflow-hidden">
      <div className="absolute inset-0 bg-black opacity-10"></div>
      <div className="max-w-7xl mx-auto relative z-10">
        <div className="flex flex-wrap items-center justify-center gap-6 text-sm font-medium">
          {/* Token Info */}
          <div className="flex items-center gap-2">
            <span className="text-yellow-200">🔥</span>
            <span className="font-bold">{tokenData.symbol}</span>
            <span className="text-yellow-200">|</span>
            <span>{tokenData.name}</span>
          </div>

          {/* Price */}
          <div className="flex items-center gap-2">
            <span className="text-yellow-200">💰</span>
            <span className="font-bold">{formatPrice(tokenData.price_usd)}</span>
            <span className="text-xs text-yellow-200">USD</span>
          </div>

          {/* Market Cap */}
          <div className="flex items-center gap-2">
            <span className="text-yellow-200">📊</span>
            <span>MC: ${formatLargeNumber(tokenData.market_cap)}</span>
          </div>

          {/* Volume */}
          <div className="flex items-center gap-2">
            <span className="text-yellow-200">📈</span>
            <span>Vol: ${formatLargeNumber(tokenData.volume_24h)}</span>
          </div>

          {/* Holders */}
          <div className="flex items-center gap-2">
            <span className="text-yellow-200">👥</span>
            <span>{formatLargeNumber(tokenData.holders)} holders</span>
          </div>

          {/* Buy Link */}
          <a
            href="https://pump.fun/mWusXdRfsYAoFtYdaDcf8tmG7hnRNvnVc2TuvNEpump"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-white bg-opacity-20 hover:bg-opacity-30 px-3 py-1 rounded-full transition-all duration-200 transform hover:scale-105 flex items-center gap-2"
          >
            <span>🚀</span>
            <span className="font-bold">BUY ON PUMP.FUN</span>
          </a>
        </div>
      </div>
      
      {/* Animated background effect */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-1/2 -right-1/2 w-96 h-96 bg-white opacity-5 rounded-full animate-pulse"></div>
        <div className="absolute -bottom-1/2 -left-1/2 w-96 h-96 bg-white opacity-5 rounded-full animate-pulse delay-1000"></div>
      </div>
    </div>
  );
};

export default PumpTokenTicker;