import React, { useState } from 'react';
import PumpTokenTicker from './PumpTokenTicker';
import { bchAuthService } from './BCHAuth';

const LoginPage = ({ onLoginSuccess, onBackToHome }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const clearCache = () => {
    // Clear all authentication-related cache
    localStorage.removeItem('bch_auth_token');
    localStorage.removeItem('accessToken');
    localStorage.removeItem('memberData');
    sessionStorage.clear();
    
    // Force reload to clear any cached state
    window.location.reload();
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    setError(''); // Clear error when user types
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Validate inputs
      if (!formData.email || !formData.password) {
        setError('Please enter both email and password');
        setLoading(false);
        return;
      }

      // Attempt login
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password
        }),
      });

      const data = await response.json();

      if (data.success) {
        // Store token
        localStorage.setItem('accessToken', data.access_token);
        localStorage.setItem('memberData', JSON.stringify(data.user));
        
        // Call success callback
        onLoginSuccess(data.user);
      } else {
        setError(data.detail || 'Login failed. Please check your credentials.');
      }
    } catch (error) {
      console.error('Login error:', error);
      
      if (error.response?.status === 401) {
        setError('Invalid email or password. Please try again.');
      } else if (error.response?.status === 404) {
        setError('Account not found. Please check your email or sign up for a new account.');
      } else {
        setError('Login failed. Please try again later.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Pump.fun Token Ticker */}
      <PumpTokenTicker />
      
      <div className="flex items-center justify-center min-h-screen pt-16 px-4">
        <div className="bg-gray-800 rounded-lg p-8 w-full max-w-md">
          {/* Header */}
          <div className="text-center mb-8">
            <img 
              src="/bitcoin-bens-logo.png" 
              alt="Bitcoin Ben's Burger Bus"
              className="w-20 h-20 mx-auto mb-4"
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
            <h1 className="text-3xl font-bold text-white mb-2">Member Login</h1>
            <p className="text-gray-400">
              Access your Bitcoin Ben's Burger Bus Club account
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-900/20 border border-red-600 rounded-lg p-4 mb-6">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-gray-400 text-sm font-medium mb-2">
                Email Address
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="Enter your email"
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-yellow-500 focus:outline-none"
                disabled={loading}
                required
              />
            </div>

            <div>
              <label className="block text-gray-400 text-sm font-medium mb-2">
                Password
              </label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="Enter your password"
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-yellow-500 focus:outline-none"
                disabled={loading}
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading || !formData.email || !formData.password}
              className="w-full py-3 bg-yellow-600 hover:bg-yellow-700 disabled:bg-gray-600 text-black font-bold rounded-lg transition-colors disabled:cursor-not-allowed"
            >
              {loading ? 'Signing In...' : 'Sign In'}
            </button>
          </form>

          {/* Additional Options */}
          <div className="mt-6 space-y-4">
            {/* Clear Cache Button */}
            <div className="text-center">
              <button
                onClick={clearCache}
                className="text-red-400 hover:text-red-300 transition-colors text-sm underline"
                title="Clear cache if you're having login issues"
              >
                🔄 Clear Cache & Refresh
              </button>
              <p className="text-gray-500 text-xs mt-1">
                Having login issues? Try clearing your cache
              </p>
            </div>
            
            <div className="text-center">
              <button
                onClick={onBackToHome}
                className="text-yellow-400 hover:text-yellow-300 transition-colors text-sm"
              >
                ← Back to Homepage
              </button>
            </div>
            
            <div className="border-t border-gray-700 pt-4">
              <p className="text-gray-400 text-sm text-center">
                Don't have an account yet?
              </p>
              <button
                onClick={onBackToHome}
                className="w-full mt-2 py-3 bg-transparent border border-yellow-600 hover:bg-yellow-600 hover:text-black text-yellow-600 font-bold rounded-lg transition-colors"
              >
                Join the Club
              </button>
            </div>
          </div>

          {/* Member Benefits Reminder */}
          <div className="mt-6 bg-yellow-900/20 border border-yellow-600 rounded-lg p-4">
            <h3 className="text-yellow-400 font-semibold text-sm mb-2">
              🎁 Member Benefits:
            </h3>
            <ul className="text-gray-300 text-xs space-y-1">
              <li>• Access to exclusive burger menu</li>
              <li>• Member-only locations and events</li>
              <li>• Crypto payment discounts</li>
              <li>• BBC Token staking rewards</li>
              <li>• Affiliate program access</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;