import React, { useState, useEffect, useMemo, useCallback } from 'react';
import './App.css';
import axios from 'axios';

// Solana wallet imports
import { ConnectionProvider, WalletProvider, useWallet } from '@solana/wallet-adapter-react';
import { WalletAdapterNetwork } from '@solana/wallet-adapter-base';
import { WalletModalProvider, WalletMultiButton, WalletDisconnectButton } from '@solana/wallet-adapter-react-ui';
import { clusterApiUrl } from '@solana/web3.js';
import { PhantomWalletAdapter, SolflareWalletAdapter } from '@solana/wallet-adapter-wallets';
import { BraveWalletAdapter } from '@solana/wallet-adapter-brave';

// Import wallet adapter CSS
import '@solana/wallet-adapter-react-ui/styles.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Service
class AuthService {
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

  async requestChallenge(address, chain = 'SOL') {
    const response = await this.apiClient.post('/api/auth/authentication/challenge', {
      address,
      chain
    });
    return response.data;
  }

  async solveChallenge(address, signature, message) {
    const response = await this.apiClient.post('/auth/authentication/solve', {
      address,
      signature,
      message
    });
    
    this.storeToken(response.data.access_token);
    return response.data;
  }

  async logout() {
    try {
      await this.apiClient.post('/auth/authentication/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      this.clearToken();
    }
  }

  storeToken(token) {
    localStorage.setItem('auth_token', token);
  }

  getStoredToken() {
    return localStorage.getItem('auth_token');
  }

  clearToken() {
    localStorage.removeItem('auth_token');
  }

  isAuthenticated() {
    return !!this.getStoredToken();
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

const authService = new AuthService();

// Wallet Authentication Component
const WalletAuth = ({ onAuthSuccess, onAuthError }) => {
  const { publicKey, signMessage, connected, disconnect } = useWallet();
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [error, setError] = useState(null);

  const handleAuthentication = useCallback(async () => {
    if (!publicKey || !signMessage) return;

    try {
      setIsAuthenticating(true);
      setError(null);

      const address = publicKey.toBase58();
      const challenge = await authService.requestChallenge(address, 'SOL');
      
      const encodedMessage = new TextEncoder().encode(challenge.message);
      const signature = await signMessage(encodedMessage);
      
      const signatureString = Array.from(signature).join(',');
      
      const authResponse = await authService.solveChallenge(
        address,
        signatureString,
        challenge.message
      );

      onAuthSuccess && onAuthSuccess(address);

    } catch (error) {
      console.error('Authentication failed:', error);
      setError(error.message || 'Authentication failed');
      onAuthError && onAuthError(error);
    } finally {
      setIsAuthenticating(false);
    }
  }, [publicKey, signMessage, onAuthSuccess, onAuthError]);

  const handleLogout = useCallback(async () => {
    await authService.logout();
    if (connected) {
      await disconnect();
    }
    window.location.reload();
  }, [connected, disconnect]);

  if (authService.isAuthenticated()) {
    return (
      <div className="flex items-center gap-4">
        <span className="text-green-400 text-sm">✓ Connected: {publicKey?.toBase58().slice(0, 8)}...</span>
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
    <div className="flex flex-col items-center gap-4">
      <WalletMultiButton className="!bg-orange-600 hover:!bg-orange-700" />
      
      {connected && publicKey && (
        <button
          onClick={handleAuthentication}
          disabled={isAuthenticating}
          className="px-6 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded-lg font-medium transition-colors"
        >
          {isAuthenticating ? 'Authenticating...' : 'Sign In to TruckMembers'}
        </button>
      )}

      {error && (
        <div className="text-red-400 text-sm bg-red-900/20 px-4 py-2 rounded">
          Error: {error}
        </div>
      )}
    </div>
  );
};

// Main App Components
const LandingPage = ({ onGetStarted }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-orange-900">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0">
          <img 
            src="https://images.unsplash.com/photo-1565123409695-7b5ef63a2efb?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzF8MHwxfHNlYXJjaHwxfHxmb29kJTIwdHJ1Y2t8ZW58MHx8fHwxNzU3NDM3MTg3fDA&ixlib=rb-4.1.0&q=85"
            alt="Food Truck"
            className="w-full h-full object-cover opacity-30"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/50 to-transparent"></div>
        </div>
        
        <div className="relative max-w-7xl mx-auto px-4 py-20 text-center">
          <h1 className="text-6xl font-bold text-white mb-6">
            Welcome to <span className="text-orange-500">TruckMembers</span>
          </h1>
          <p className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
            Join our exclusive food truck community. Get access to premium gourmet meals, 
            member-only locations, tax-free pricing, and special events.
          </p>
          
          <div className="flex flex-col items-center gap-6">
            <button
              onClick={onGetStarted}
              className="px-8 py-4 bg-orange-600 hover:bg-orange-700 text-white text-lg font-bold rounded-lg transition-colors transform hover:scale-105"
            >
              Connect Wallet & Join
            </button>
            
            <div className="text-gray-400 text-sm">
              🔐 Secure blockchain authentication with Solana wallets
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-4 py-16">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          <div className="text-center">
            <div className="w-16 h-16 bg-orange-600 rounded-full flex items-center justify-center mx-auto mb-4">
              🍕
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Exclusive Menus</h3>
            <p className="text-gray-400">Access premium gourmet items not available to the public</p>
          </div>
          
          <div className="text-center">
            <div className="w-16 h-16 bg-orange-600 rounded-full flex items-center justify-center mx-auto mb-4">
              📍
            </div>
            <h3 className="text-xl font-bold text-white mb-2">VIP Locations</h3>
            <p className="text-gray-400">Member-only food truck stops and private events</p>
          </div>
          
          <div className="text-center">
            <div className="w-16 h-16 bg-orange-600 rounded-full flex items-center justify-center mx-auto mb-4">
              💰
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Tax-Free Pricing</h3>
            <p className="text-gray-400">Special member pricing on all premium items</p>
          </div>
          
          <div className="text-center">
            <div className="w-16 h-16 bg-orange-600 rounded-full flex items-center justify-center mx-auto mb-4">
              🎉
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Exclusive Events</h3>
            <p className="text-gray-400">Chef's table experiences and wine pairings</p>
          </div>
        </div>
      </div>

      {/* Sample Menu Preview */}
      <div className="bg-gray-800/50 py-16">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-4xl font-bold text-white text-center mb-12">Premium Menu Preview</h2>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-gray-800 rounded-lg overflow-hidden">
              <img 
                src="https://images.unsplash.com/photo-1628838463043-b81a343794d6?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwyfHxnb3VybWV0JTIwZm9vZHxlbnwwfHx8fDE3NTc0MzcyMDJ8MA&ixlib=rb-4.1.0&q=85"
                alt="Artisanal Fruit Bowl"
                className="w-full h-48 object-cover"
              />
              <div className="p-6">
                <h3 className="text-xl font-bold text-white mb-2">Artisanal Fruit Bowl</h3>
                <p className="text-gray-400 mb-4">Seasonal fruits with edible flowers</p>
                <div className="flex justify-between items-center">
                  <span className="text-orange-500 font-bold">$9 (Members)</span>
                  <span className="text-gray-400 line-through">$12 (Public)</span>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-800 rounded-lg overflow-hidden">
              <img 
                src="https://images.unsplash.com/photo-1623073284788-0d846f75e329?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHwxfHxnb3VybWV0JTIwZm9vZHxlbnwwfHx8fDE3NTc0MzcyMDJ8MA&ixlib=rb-4.1.0&q=85"
                alt="Truffle Mac & Cheese"
                className="w-full h-48 object-cover"
              />
              <div className="p-6">
                <h3 className="text-xl font-bold text-white mb-2">Truffle Mac & Cheese</h3>
                <p className="text-gray-400 mb-4">Artisanal with truffle oil & parmesan</p>
                <div className="flex justify-between items-center">
                  <span className="text-orange-500 font-bold">$14 (Members)</span>
                  <span className="text-gray-400 line-through">$18 (Public)</span>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-800 rounded-lg overflow-hidden border-2 border-orange-600">
              <img 
                src="https://images.unsplash.com/photo-1616671285410-2a676a9a433d?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDk1Nzd8MHwxfHNlYXJjaHw0fHxnb3VybWV0JTIwZm9vZHxlbnwwfHx8fDE3NTc0MzcyMDJ8MA&ixlib=rb-4.1.0&q=85"
                alt="Wagyu Beef Sliders"
                className="w-full h-48 object-cover"
              />
              <div className="p-6">
                <h3 className="text-xl font-bold text-white mb-2">Wagyu Beef Slider Trio</h3>
                <p className="text-gray-400 mb-2">Premium wagyu with gourmet toppings</p>
                <div className="text-orange-400 text-sm mb-4">🥇 Premium Members Only</div>
                <div className="flex justify-between items-center">
                  <span className="text-orange-500 font-bold">$22 (Members)</span>
                  <span className="text-gray-400 line-through">$28 (Public)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const MemberDashboard = ({ memberAddress }) => {
  const [memberData, setMemberData] = useState(null);
  const [menu, setMenu] = useState([]);
  const [locations, setLocations] = useState([]);
  const [events, setEvents] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('menu');

  useEffect(() => {
    const loadMemberData = async () => {
      try {
        setLoading(true);
        
        // Seed sample data first
        await authService.post('/api/admin/seed-data');
        
        // Load member data
        const [profile, menuData, locationsData, eventsData, ordersData] = await Promise.all([
          authService.get('/api/profile'),
          authService.get('/api/menu/member'),
          authService.get('/api/locations/member'),
          authService.get('/api/events'),
          authService.get('/api/orders')
        ]);

        setMemberData(profile);
        setMenu(menuData);
        setLocations(locationsData);
        setEvents(eventsData);
        setOrders(ordersData);
      } catch (error) {
        console.error('Error loading member data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadMemberData();
  }, []);

  const handlePreOrder = async (item, quantity = 1) => {
    try {
      const orderItems = [{
        item_id: item.id,
        quantity: quantity,
        special_instructions: ""
      }];

      await authService.post('/api/orders', {
        items: orderItems,
        pickup_location: "Downtown Business District",
        pickup_time: "12:00"
      });

      alert('Order placed successfully!');
      
      // Refresh orders
      const ordersData = await authService.get('/api/orders');
      setOrders(ordersData);
    } catch (error) {
      console.error('Order failed:', error);
      alert('Order failed. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading your member dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-white">Member Dashboard</h1>
              <p className="text-gray-400">Welcome back, {memberAddress?.slice(0, 8)}...</p>
            </div>
            <WalletAuth />
          </div>
        </div>
      </div>

      {/* Member Stats */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="text-orange-500 text-2xl font-bold">{memberData?.membership_tier?.toUpperCase()}</div>
            <div className="text-gray-400">Membership Tier</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="text-orange-500 text-2xl font-bold">{memberData?.total_orders || 0}</div>
            <div className="text-gray-400">Total Orders</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="text-orange-500 text-2xl font-bold">{locations.length}</div>
            <div className="text-gray-400">Available Locations</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="text-orange-500 text-2xl font-bold">{events.length}</div>
            <div className="text-gray-400">Exclusive Events</div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1 bg-gray-800 rounded-lg p-1 mb-6">
          {['menu', 'locations', 'events', 'orders'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-3 rounded-md font-medium capitalize transition-colors ${
                activeTab === tab
                  ? 'bg-orange-600 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'menu' && (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {menu.map((item) => (
              <div key={item.id} className="bg-gray-800 rounded-lg overflow-hidden">
                <img 
                  src={item.image_url}
                  alt={item.name}
                  className="w-full h-48 object-cover"
                />
                <div className="p-6">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-xl font-bold text-white">{item.name}</h3>
                    {item.tier_required !== 'basic' && (
                      <span className="text-xs bg-orange-600 text-white px-2 py-1 rounded">
                        {item.tier_required.toUpperCase()}
                      </span>
                    )}
                  </div>
                  <p className="text-gray-400 mb-4">{item.description}</p>
                  <div className="flex justify-between items-center mb-4">
                    <div>
                      <span className="text-orange-500 font-bold text-lg">${item.member_price}</span>
                      <span className="text-gray-400 line-through ml-2">${item.price}</span>
                    </div>
                    <span className="text-green-400 text-sm">
                      Save ${(item.price - item.member_price).toFixed(2)}
                    </span>
                  </div>
                  <button
                    onClick={() => handlePreOrder(item)}
                    className="w-full bg-orange-600 hover:bg-orange-700 text-white py-2 rounded-lg font-medium transition-colors"
                  >
                    Pre-Order Now
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'locations' && (
          <div className="grid md:grid-cols-2 gap-6">
            {locations.map((location) => (
              <div key={location.id} className="bg-gray-800 rounded-lg p-6">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-xl font-bold text-white">{location.name}</h3>
                  {location.is_member_exclusive && (
                    <span className="text-xs bg-orange-600 text-white px-2 py-1 rounded">
                      MEMBERS ONLY
                    </span>
                  )}
                </div>
                <p className="text-gray-400 mb-2">📍 {location.address}</p>
                <p className="text-gray-400 mb-2">📅 {location.date}</p>
                <p className="text-gray-400">⏰ {location.start_time} - {location.end_time}</p>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'events' && (
          <div className="grid md:grid-cols-2 gap-6">
            {events.map((event) => (
              <div key={event.id} className="bg-gray-800 rounded-lg p-6">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-xl font-bold text-white">{event.title}</h3>
                  <span className="text-xs bg-orange-600 text-white px-2 py-1 rounded">
                    {event.tier_required.toUpperCase()}
                  </span>
                </div>
                <p className="text-gray-400 mb-4">{event.description}</p>
                <div className="text-gray-400 mb-4">
                  <p>📅 {event.date} at {event.time}</p>
                  <p>📍 {event.location}</p>
                  <p>👥 {event.current_attendees}/{event.max_attendees} attendees</p>
                </div>
                <button className="w-full bg-orange-600 hover:bg-orange-700 text-white py-2 rounded-lg font-medium transition-colors">
                  Join Event
                </button>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'orders' && (
          <div className="space-y-4">
            {orders.length === 0 ? (
              <div className="text-center text-gray-400 py-12">
                <p>No orders yet. Start by ordering from the menu!</p>
              </div>
            ) : (
              orders.map((order) => (
                <div key={order.id} className="bg-gray-800 rounded-lg p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-xl font-bold text-white">Order #{order.id.slice(0, 8)}</h3>
                      <p className="text-gray-400">Pickup: {order.pickup_time} at {order.pickup_location}</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm ${
                      order.status === 'pending' ? 'bg-yellow-600 text-yellow-100' :
                      order.status === 'confirmed' ? 'bg-blue-600 text-blue-100' :
                      order.status === 'ready' ? 'bg-green-600 text-green-100' :
                      'bg-gray-600 text-gray-100'
                    }`}>
                      {order.status.toUpperCase()}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-orange-500 font-bold text-lg">${order.total_amount.toFixed(2)}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Wallet Provider Setup
const WalletProviders = ({ children }) => {
  const network = WalletAdapterNetwork.Devnet;
  const endpoint = useMemo(() => clusterApiUrl(network), [network]);
  
  const wallets = useMemo(
    () => [
      new PhantomWalletAdapter(),
      new SolflareWalletAdapter({ network }),
      new BraveWalletAdapter(),
    ],
    [network]
  );

  return (
    <ConnectionProvider endpoint={endpoint}>
      <WalletProvider wallets={wallets} autoConnect>
        <WalletModalProvider>
          {children}
        </WalletModalProvider>
      </WalletProvider>
    </ConnectionProvider>
  );
};

// Main App
function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [memberAddress, setMemberAddress] = useState(null);
  const [showAuth, setShowAuth] = useState(false);

  useEffect(() => {
    const checkAuth = () => {
      const authenticated = authService.isAuthenticated();
      setIsAuthenticated(authenticated);
      
      if (authenticated) {
        // In a real app, decode JWT to get address
        const token = authService.getStoredToken();
        if (token) {
          try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            setMemberAddress(payload.sub);
          } catch (e) {
            console.error('Token decode error:', e);
          }
        }
      }
    };

    checkAuth();
  }, []);

  const handleAuthSuccess = (address) => {
    setIsAuthenticated(true);
    setMemberAddress(address);
    setShowAuth(false);
  };

  const handleAuthError = (error) => {
    console.error('Auth error:', error);
  };

  if (isAuthenticated && memberAddress) {
    return (
      <WalletProviders>
        <MemberDashboard memberAddress={memberAddress} />
      </WalletProviders>
    );
  }

  if (showAuth) {
    return (
      <WalletProviders>
        <div className="min-h-screen bg-gray-900 flex items-center justify-center">
          <div className="bg-gray-800 rounded-lg p-8 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold text-white text-center mb-6">
              Connect Your Solana Wallet
            </h2>
            <p className="text-gray-400 text-center mb-8">
              Sign a message with your wallet to prove ownership and join TruckMembers
            </p>
            
            <WalletAuth 
              onAuthSuccess={handleAuthSuccess}
              onAuthError={handleAuthError}
            />
            
            <button
              onClick={() => setShowAuth(false)}
              className="w-full mt-4 text-gray-400 hover:text-white transition-colors"
            >
              ← Back to landing page
            </button>
          </div>
        </div>
      </WalletProviders>
    );
  }

  return (
    <WalletProviders>
      <LandingPage onGetStarted={() => setShowAuth(true)} />
    </WalletProviders>
  );
}

export default App;