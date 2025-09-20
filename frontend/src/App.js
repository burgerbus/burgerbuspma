import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import { BCHAuthentication, bchAuthService } from './BCHAuth';
import AdminPanel from './AdminPanel';
import WalletDebug from './WalletDebug';
import P2PPaymentSelector from './P2PPaymentSelector';
import AffiliateDashboard from './AffiliateDashboard';
import PumpTokenTicker from './PumpTokenTicker';
import { BBCStakingProvider } from './BBCStakingProvider';
import BBCStakingInterface from './BBCStakingInterface';
import LoginPage from './LoginPage';
import SolanaWalletProvider from './SolanaWalletProvider';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// PMA Agreement Page Component
const PMAgreementPage = ({ memberAddress, onComplete }) => {
  const [agreed, setAgreed] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [step, setStep] = useState('agreement'); // agreement, payment, waiting
  const [paymentData, setPaymentData] = useState(null);
  const [memberInfo, setMemberInfo] = useState({
    fullName: '',
    email: '',
    phone: '',
    password: '',
    referralCode: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!agreed) {
      alert('Please read and accept the PMA agreement to continue.');
      return;
    }

    setProcessing(true);
    
    try {
      // Since membership is free, register member immediately
      const registrationData = {
        name: memberInfo.fullName,
        email: memberInfo.email,
        password: memberInfo.password,
        phone: memberInfo.phone || '',
        address: '',  // Optional field not in current form
        city: '',     // Optional field not in current form  
        state: '',    // Optional field not in current form
        zip_code: '', // Optional field not in current form
        pma_agreed: agreed,
        referral_code: memberInfo.referralCode || ''
      };
      
      const response = await bchAuthService.post('/api/auth/register', registrationData);
      
      if (response.success) {
        // Store token using the same key as bchAuthService expects
        localStorage.setItem('bch_auth_token', response.access_token);
        localStorage.setItem('accessToken', response.access_token); // Keep for compatibility
        localStorage.setItem('memberData', JSON.stringify(response.user));
        
        alert('🎉 Welcome to Bitcoin Ben\'s Burger Bus Club! Your FREE membership is active!');
        onComplete(response.user);
      } else {
        throw new Error('Registration failed');
      }
    } catch (error) {
      console.error('Registration error:', error);
      alert(`Registration failed: ${error.response?.data?.detail || error.message}. Please try again.`);
      setProcessing(false);
    }
  };

  const handlePaymentComplete = () => {
    setStep('waiting');
    // Poll for payment status every 30 seconds
    const pollInterval = setInterval(async () => {
      try {
        const status = await bchAuthService.get(`/api/payments/status/${paymentData.payment_id}`);
        if (status.status === 'verified') {
          clearInterval(pollInterval);
          alert('Payment verified! Welcome to Bitcoin Ben\'s Burger Bus Club!');
          onComplete();
        }
      } catch (error) {
        console.error('Status check failed:', error);
      }
    }, 30000);

    // Clean up interval after 1 hour
    setTimeout(() => clearInterval(pollInterval), 3600000);
  };

  if (step === 'payment') {
    return (
      <div className="min-h-screen bg-gray-900">
        {/* Pump.fun Token Ticker */}
        <PumpTokenTicker />
        
        <div className="py-12 px-4">
          <div className="max-w-4xl mx-auto">
            <div className="bg-gray-800 rounded-lg p-8">
              <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-white mb-4">
                Complete Your <span className="text-orange-500">PMA Membership</span>
              </h1>
              <p className="text-gray-400">
                Choose your preferred peer-to-peer payment method
              </p>
            </div>

              <P2PPaymentSelector
                memberEmail={memberInfo.email}
                onPaymentSelected={(paymentData) => {
                  console.log('Payment selected:', paymentData);
                  // Could store payment data or update state as needed
                }}
              />

              <div className="mt-8 text-center">
                <button
                  onClick={() => setStep('agreement')}
                  className="text-orange-400 hover:text-orange-300 transition-colors"
                >
                  ← Back to PMA Agreement
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (step === 'waiting') {
    return (
      <div className="min-h-screen bg-gray-900">
        {/* Pump.fun Token Ticker */}
        <PumpTokenTicker />
        
        <div className="flex items-center justify-center min-h-screen pt-16">
          <div className="bg-gray-800 rounded-lg p-8 max-w-md w-full mx-4 text-center">
          <div className="text-6xl mb-4">⏳</div>
          <h2 className="text-2xl font-bold text-white mb-4">Payment Submitted!</h2>
          <p className="text-gray-400 mb-6">
            We've received your payment notification. Our admin will verify your BCH payment and activate your membership within 24 hours.
          </p>
          <div className="bg-blue-900/20 border border-blue-600 rounded-lg p-4">
            <p className="text-blue-400 font-medium">📧 You'll receive:</p>
            <ul className="text-gray-300 text-sm mt-2 space-y-1">
              <li>• Membership activation confirmation</li>
              <li>• $15 BCH cashstamp bonus</li>
              <li>• Access to exclusive menu and locations</li>
            </ul>
          </div>
          <button
            onClick={() => setStep('agreement')}
            className="mt-6 text-orange-400 hover:text-orange-300 transition-colors"
          >
            ← Back to agreement
          </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Pump.fun Token Ticker */}
      <PumpTokenTicker />
      
      <div className="py-8 sm:py-12 px-3 sm:px-4">
        <div className="max-w-4xl mx-auto">
          <div className="bg-gray-800 rounded-lg p-4 sm:p-8">
          <div className="text-center mb-6 sm:mb-8">
            <h1 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Welcome to <span className="text-orange-500">Bitcoin Ben's</span><br />
              Burger Bus Club
            </h1>
            <p className="text-gray-400 text-sm sm:text-base">
              Complete your FREE membership by signing our Private Membership Agreement
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">{/* Rest of the original PMA form stays the same */}
            {/* Member Information */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
              <div>
                <label className="block text-white font-medium mb-2 text-sm sm:text-base">Full Name *</label>
                <input
                  type="text"
                  required
                  value={memberInfo.fullName}
                  onChange={(e) => setMemberInfo({...memberInfo, fullName: e.target.value})}
                  className="w-full px-3 py-3 sm:px-4 sm:py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-orange-500 focus:outline-none text-base"
                  placeholder="Enter your full name"
                />
              </div>
              <div>
                <label className="block text-white font-medium mb-2 text-sm sm:text-base">Email Address *</label>
                <input
                  type="email"
                  required
                  value={memberInfo.email}
                  onChange={(e) => setMemberInfo({...memberInfo, email: e.target.value})}
                  className="w-full px-3 py-3 sm:px-4 sm:py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-orange-500 focus:outline-none text-base"
                  placeholder="Enter your email"
                />
              </div>
              <div>
                <label className="block text-white font-medium mb-2 text-sm sm:text-base">Password *</label>
                <input
                  type="password"
                  required
                  value={memberInfo.password}
                  onChange={(e) => setMemberInfo({...memberInfo, password: e.target.value})}
                  className="w-full px-3 py-3 sm:px-4 sm:py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-orange-500 focus:outline-none text-base"
                  placeholder="Create a password"
                />
              </div>
              <div>
                <label className="block text-white font-medium mb-2 text-sm sm:text-base">
                  Referral Code <span className="text-yellow-400">(Optional - Earn $3!)</span>
                </label>
                <input
                  type="text"
                  value={memberInfo.referralCode}
                  onChange={(e) => setMemberInfo({...memberInfo, referralCode: e.target.value.toUpperCase()})}
                  className="w-full px-3 py-3 sm:px-4 sm:py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-yellow-500 focus:outline-none text-base"
                  placeholder="BITCOINBEN-XXXX (optional)"
                />
                <p className="text-xs text-gray-400 mt-1">
                  Have a referral code? The member who referred you earns $3 commission!
                </p>
              </div>
            </div>

            <div>
              <label className="block text-white font-medium mb-2 text-sm sm:text-base">Phone Number (Optional)</label>
              <input
                type="tel"
                value={memberInfo.phone}
                onChange={(e) => setMemberInfo({...memberInfo, phone: e.target.value})}
                className="w-full px-3 py-3 sm:px-4 sm:py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-orange-500 focus:outline-none text-base"
                placeholder="Enter your phone number"
              />
            </div>

            {/* PMA Agreement */}
            <div className="bg-gray-700 p-6 rounded-lg max-h-96 overflow-y-auto">
              <h2 className="text-xl font-bold text-white mb-4">Private Membership Agreement</h2>
              <div className="text-gray-300 space-y-4 text-sm leading-relaxed">
                <p>
                  <strong>Bitcoin Ben's Burger Bus Club - Private Membership Agreement</strong>
                </p>
                <p>
                  This Private Membership Agreement ("Agreement") is entered into between Bitcoin Ben's Burger Bus Club, 
                  a private membership association ("Club"), and the undersigned ("Member").
                </p>
                <p>
                  <strong>1. PRIVATE MEMBERSHIP ASSOCIATION</strong><br />
                  The Club is a private membership association operating under the right of private contract and association. 
                  Membership is by invitation only and subject to acceptance of this Agreement.
                </p>
                <p>
                  <strong>2. MEMBERSHIP BENEFITS</strong><br />
                  Members enjoy exclusive access to premium gourmet burgers, crypto-friendly dining experiences, 
                  member-only locations, special Bitcoin events, and discounted pricing on all menu items.
                </p>
                <p>
                  <strong>3. MEMBERSHIP DUES</strong><br />
                  Membership is currently FREE! Simply complete the PMA agreement to join. 
                  Dues are non-refundable and provide access to all club benefits for one year.
                </p>
                <p>
                  <strong>4. PRIVACY & CONDUCT</strong><br />
                  Members agree to maintain the privacy of club operations and respect fellow members. 
                  The Club reserves the right to terminate membership for violations of club policies.
                </p>
                <p>
                  <strong>5. MEMBERSHIP AUTHENTICATION</strong><br />
                  Membership is tied to your email address: <code className="bg-gray-600 px-2 py-1 rounded text-orange-400">{memberInfo.email}</code>
                </p>
                <p>
                  <strong>6. LIMITATION OF LIABILITY</strong><br />
                  Members participate at their own risk. The Club limits liability to the maximum extent permitted by law.
                </p>
                <p className="text-orange-400 font-medium">
                  By checking the box below, you acknowledge that you have read, understood, and agree to be bound by this Agreement.
                </p>
              </div>
            </div>

            {/* Agreement Checkbox */}
            <div className="flex items-start space-x-3">
              <input
                type="checkbox"
                id="pma-agreement"
                checked={agreed}
                onChange={(e) => setAgreed(e.target.checked)}
                className="mt-1 w-4 h-4 text-orange-600 bg-gray-700 border-gray-600 rounded focus:ring-orange-500"
              />
              <label htmlFor="pma-agreement" className="text-white">
                I have read and agree to the Private Membership Agreement and understand that by joining, 
                I am entering into a private contract with Bitcoin Ben's Burger Bus Club.
              </label>
            </div>

            {/* Payment Information */}
            <div className="bg-orange-900/20 border border-orange-600 rounded-lg p-6">
              <h3 className="text-xl font-bold text-orange-400 mb-2">Membership Investment</h3>
              <div className="flex justify-between items-center text-white">
                <span>Annual Membership Dues:</span>
                <span className="text-2xl font-bold text-green-400">FREE</span>
              </div>
              <p className="text-gray-400 text-sm mt-2">
                Payment processing via P2P payment methods. Your membership activates immediately upon agreement.
              </p>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={!agreed || processing}
              className="w-full bg-orange-600 hover:bg-orange-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white py-4 rounded-lg font-bold text-base sm:text-lg transition-colors"
            >
              {processing ? 'Processing Membership...' : 'Join Club - FREE Membership'}
            </button>
          </form>
        </div>
        </div>
      </div>
    </div>
  );
};

// Main App Components
const LandingPage = ({ onGetStarted, onMemberLogin }) => {
  // Default: Render LandingPage (lowest priority)
  console.log('RENDERING: LandingPage (default fallback)');
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-orange-900">
      {/* Pump.fun Token Ticker */}
      <PumpTokenTicker />
      
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0">
          <img 
            src="https://images.unsplash.com/photo-1550547660-d9450f859349?crop=entropy&cs=srgb&fm=jpg&q=85"
            alt="Premium Gourmet Burgers"
            className="w-full h-full object-cover opacity-40"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/70 to-gray-900/30"></div>
        </div>
        
        <div className="relative max-w-7xl mx-auto px-4 py-12 sm:py-20 text-center">
          <div className="flex flex-col items-center mb-6">
            <img 
              src="/bitcoin-bens-logo.png" 
              alt="Bitcoin Ben's Burger Bus"
              className="w-24 h-24 sm:w-32 sm:h-32 mb-4"
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
            <h1 className="text-4xl sm:text-6xl font-bold text-white text-center">
              <span className="text-yellow-400">Bitcoin Ben's</span><br />
              <span className="text-white">Burger Bus Club</span>
            </h1>
          </div>
          <p className="text-lg sm:text-xl text-gray-300 mb-6 sm:mb-8 max-w-3xl mx-auto px-4 sm:px-0">
            Join Bitcoin Ben's exclusive burger club. Get access to premium gourmet burgers, 
            crypto-friendly dining, member-only locations, and special Bitcoin events.
          </p>
          
          <div className="flex flex-col items-center gap-4 sm:gap-6">
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 w-full max-w-md sm:max-w-none">
              <button
                onClick={onGetStarted}
                className="px-6 py-4 sm:px-8 bg-yellow-600 hover:bg-yellow-700 text-black text-lg font-bold rounded-lg transition-colors transform hover:scale-105 w-full sm:w-auto"
              >
                Join the Club
              </button>
              
              <button
                onClick={onMemberLogin}
                className="px-6 py-4 sm:px-8 bg-transparent border-2 border-yellow-600 hover:bg-yellow-600 hover:text-black text-yellow-600 text-lg font-bold rounded-lg transition-colors transform hover:scale-105 w-full sm:w-auto"
              >
                Member Login
              </button>
            </div>
            
            <div className="text-gray-400 text-sm text-center px-4">
              🔐 Private Membership Association with P2P payment options | 🍔 Premium Bitcoin Burgers<br/>
              <span className="text-yellow-400">Existing members:</span> Use your email and password to access your dashboard
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="max-w-7xl mx-auto px-4 py-12 sm:py-16">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
          <div className="text-center">
            <div className="w-16 h-16 bg-yellow-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
              🍔
            </div>
            <h3 className="text-lg sm:text-xl font-bold text-white mb-2">Bitcoin Burgers</h3>
            <p className="text-gray-400 text-sm sm:text-base">Exclusive gourmet burgers crafted for crypto enthusiasts</p>
          </div>
          
          <div className="text-center">
            <div className="w-16 h-16 bg-yellow-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
              📍
            </div>
            <h3 className="text-lg sm:text-xl font-bold text-white mb-2">Crypto Meetups</h3>
            <p className="text-gray-400 text-sm sm:text-base">Exclusive stops at Bitcoin conferences and crypto events</p>
          </div>
          
          <div className="text-center">
            <div className="w-16 h-16 bg-yellow-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
              💰
            </div>
            <h3 className="text-lg sm:text-xl font-bold text-white mb-2">Crypto Pricing</h3>
            <p className="text-gray-400 text-sm sm:text-base">Pay with crypto and get exclusive member discounts</p>
          </div>
          
          <div className="text-center">
            <div className="w-16 h-16 bg-yellow-600 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
              🎉
            </div>
            <h3 className="text-lg sm:text-xl font-bold text-white mb-2">Bitcoin Events</h3>
            <p className="text-gray-400 text-sm sm:text-base">Private dining and crypto education sessions</p>
          </div>
        </div>
      </div>

      {/* Graphic Menu Section */}
      <div className="bg-gray-800/50 py-12 sm:py-16">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-3xl sm:text-4xl font-bold text-white text-center mb-8 sm:mb-12">Bitcoin Ben's Exclusive Menu</h2>
          
          <div className="max-w-4xl mx-auto">
            <div className="bg-gray-800 rounded-lg overflow-hidden shadow-2xl border border-orange-600/30">
              <img 
                src="https://images.unsplash.com/photo-1629341948402-42a2d20577a6?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzB8MHwxfHNlYXJjaHwxfHxidXJnZXIlMjBtZW51fGVufDB8fHx8MTc1ODMyMzY5OXww&ixlib=rb-4.1.0&q=85"
                alt="Bitcoin Ben's Burger Bus Club Menu"
                className="w-full h-96 sm:h-[500px] lg:h-[600px] object-cover"
              />
              <div className="p-4 sm:p-6 text-center bg-gradient-to-t from-gray-900 to-gray-800">
                <h3 className="text-xl sm:text-2xl font-bold text-orange-400 mb-2">Premium Bitcoin-Themed Menu</h3>
                <p className="text-gray-300 mb-4 text-sm sm:text-base">
                  Featuring exclusive gourmet burgers, crypto-inspired dishes, and member-only pricing
                </p>
                <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center items-center">
                  <div className="text-orange-500 font-bold text-base sm:text-lg">
                    🔐 Members Only Pricing & Access
                  </div>
                  <button
                    onClick={onGetStarted}
                    className="px-6 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg font-medium transition-colors text-sm sm:text-base"
                  >
                    Join to View Full Menu
                  </button>
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
  const [showPMAPage, setShowPMAPage] = useState(false);

  useEffect(() => {
    const loadMemberData = async () => {
      try {
        setLoading(true);
        
        // Seed sample data first
        await bchAuthService.post('/api/admin/seed-data');
        
        // Try to load member profile first (using real authenticated endpoint)
        let profile;
        try {
          profile = await bchAuthService.get('/api/profile');
        } catch (profileError) {
          console.error('Profile fetch error:', profileError);
          // If profile doesn't exist, show PMA page
          console.log('No profile found, showing PMA page');
          setShowPMAPage(true);
          setLoading(false);
          return;
        }

        // Load member data (using debug endpoints temporarily)
        const [menuData, locationsData, eventsData, ordersData] = await Promise.all([
          bchAuthService.get('/api/debug/menu'),
          bchAuthService.get('/api/debug/locations'),
          bchAuthService.get('/api/debug/events'),
          bchAuthService.get('/api/debug/orders')
        ]);

        setMemberData(profile);
        setMenu(menuData);
        setLocations(locationsData);
        setEvents(eventsData);
        setOrders(ordersData);
        
        // Check if member has completed PMA requirements
        if (!profile.pma_agreed || !profile.dues_paid) {
          console.log('Member has not completed PMA requirements:', { pma_agreed: profile.pma_agreed, dues_paid: profile.dues_paid });
          setShowPMAPage(true);
        } else {
          console.log('Member has completed PMA requirements, showing dashboard');
        }
      } catch (error) {
        console.error('Error loading member data:', error);
        
        // Only show PMA page if it's an authentication issue
        if (error.response?.status === 401 || error.response?.status === 403) {
          console.log('Authentication error, showing PMA page');
          setShowPMAPage(true);
        } else {
          // For other errors, show dashboard with empty data
          console.log('Non-auth error, showing dashboard with limited data');
          setMenu([]);
          setLocations([]);
          setEvents([]);
          setOrders([]);
        }
      } finally {
        setLoading(false);
      }
    };

    loadMemberData();
  }, []);

  const handlePreOrder = async (item, quantity = 1) => {
    // Check if member has completed PMA requirements
    if (!memberData || !memberData.pma_agreed || !memberData.dues_paid) {
      alert('You must complete your FREE PMA membership agreement before placing orders. Please complete your registration first.');
      setShowPMAPage(true);
      return;
    }

    try {
      const orderItems = [{
        item_id: item.id,
        quantity: quantity,
        special_instructions: ""
      }];

      await bchAuthService.post('/api/orders', {
        items: orderItems,
        pickup_location: "Downtown Business District",
        pickup_time: "12:00"
      });

      alert('Order placed successfully!');
      
      // Refresh orders
      const ordersData = await bchAuthService.get('/api/orders');
      setOrders(ordersData);
    } catch (error) {
      console.error('Order failed:', error);
      
      if (error.response?.status === 403) {
        // Backend validation failed - show PMA page
        alert(error.response.data.detail || 'Please complete your membership requirements before ordering.');
        setShowPMAPage(true);
      } else {
        alert('Order failed. Please try again.');
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading your member dashboard...</div>
      </div>
    );
  }

  // Show PMA agreement page if needed
  if (showPMAPage) {
    return <PMAgreementPage memberAddress={memberAddress} onComplete={() => {
      setShowPMAPage(false);
      // Reload member data after PMA completion
      const loadMemberData = async () => {
        try {
          const [profile, menuData, locationsData, eventsData, ordersData] = await Promise.all([
            bchAuthService.get('/api/profile'),
            bchAuthService.get('/api/debug/menu'),
            bchAuthService.get('/api/debug/locations'),
            bchAuthService.get('/api/debug/events'),
            bchAuthService.get('/api/debug/orders')
          ]);

          setMemberData(profile);
          setMenu(menuData);
          setLocations(locationsData);
          setEvents(eventsData);
          setOrders(ordersData);
        } catch (error) {
          console.error('Error reloading member data:', error);
        }
      };
      loadMemberData();
    }} />;
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Pump.fun Token Ticker */}
      <PumpTokenTicker />
      
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:py-6">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
            <div className="flex-1 min-w-0">
              <h1 className="text-2xl sm:text-3xl font-bold text-white truncate">Club Dashboard</h1>
              <p className="text-gray-400 text-sm sm:text-base truncate">Welcome to Bitcoin Ben's, {memberData?.full_name || 'Member'}!</p>
            </div>
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4">
              <span className="text-green-400 text-xs sm:text-sm truncate">✓ {memberData?.email || 'Member'}</span>
              <button
                onClick={() => {
                  // Clear any stored tokens
                  localStorage.clear();
                  // Reload page to reset state
                  window.location.reload();
                }}
                className="px-3 py-2 sm:px-4 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm transition-colors w-full sm:w-auto"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Member Stats */}
      <div className="max-w-7xl mx-auto px-3 sm:px-4 py-4 sm:py-6">
        {/* PMA Status Warning */}
        {memberData && (!memberData.pma_agreed || !memberData.dues_paid) && (
          <div className="bg-red-900/20 border border-red-500 rounded-lg p-4 mb-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="flex-1 min-w-0">
                <h3 className="text-red-400 font-bold text-base sm:text-lg">⚠️ Membership Incomplete</h3>
                <p className="text-red-300 text-sm sm:text-base">
                  {!memberData.pma_agreed && !memberData.dues_paid 
                    ? "Please complete your FREE PMA agreement to start ordering."
                    : !memberData.pma_agreed 
                    ? "Please complete your FREE PMA agreement to start ordering."
                    : "Welcome! Your FREE membership is active - start ordering!"
                  }
                </p>
              </div>
              <button
                onClick={() => setShowPMAPage(true)}
                className="px-4 py-2 sm:px-6 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors w-full sm:w-auto text-sm sm:text-base"
              >
                Complete Membership
              </button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6 mb-6 sm:mb-8">
          <div className="bg-gray-800 rounded-lg p-4 sm:p-6">
            <div className="text-orange-500 text-lg sm:text-2xl font-bold">{memberData?.membership_tier?.toUpperCase()}</div>
            <div className="text-gray-400 text-sm sm:text-base">Membership Tier</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 sm:p-6">
            <div className="text-orange-500 text-lg sm:text-2xl font-bold">{memberData?.total_orders || 0}</div>
            <div className="text-gray-400 text-sm sm:text-base">Total Orders</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 sm:p-6">
            <div className="text-orange-500 text-lg sm:text-2xl font-bold">{locations.length}</div>
            <div className="text-gray-400 text-sm sm:text-base">Available Locations</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4 sm:p-6">
            <div className={`text-lg sm:text-2xl font-bold ${memberData?.pma_agreed && memberData?.dues_paid ? 'text-green-500' : 'text-red-500'}`}>
              {memberData?.pma_agreed && memberData?.dues_paid ? '✅' : '❌'}
            </div>
            <div className="text-gray-400 text-sm sm:text-base">PMA Status</div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-gray-800 rounded-lg p-1 mb-6 overflow-x-auto">
          <div className="flex space-x-1 min-w-max">
            {['menu', 'locations', 'events', 'orders', 'affiliates', 'staking'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-2 sm:px-6 sm:py-3 rounded-md font-medium capitalize transition-colors whitespace-nowrap text-sm sm:text-base ${
                  activeTab === tab
                    ? 'bg-orange-600 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {tab === 'staking' ? '🪙 BBC Staking' : tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'menu' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {menu.map((item) => (
              <div key={item.id} className="bg-gray-800 rounded-lg overflow-hidden">
                <img 
                  src={item.image_url}
                  alt={item.name}
                  className="w-full h-40 sm:h-48 object-cover"
                />
                <div className="p-4 sm:p-6">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-lg sm:text-xl font-bold text-white flex-1 pr-2">{item.name}</h3>
                    {item.tier_required !== 'basic' && (
                      <span className="text-xs bg-orange-600 text-white px-2 py-1 rounded flex-shrink-0">
                        {item.tier_required.toUpperCase()}
                      </span>
                    )}
                  </div>
                  <p className="text-gray-400 mb-4 text-sm sm:text-base">{item.description}</p>
                  <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-4 gap-2">
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
                    disabled={!memberData?.pma_agreed || !memberData?.dues_paid}
                    className={`w-full py-3 sm:py-2 rounded-lg font-medium transition-colors text-sm sm:text-base ${
                      memberData?.pma_agreed && memberData?.dues_paid
                        ? 'bg-orange-600 hover:bg-orange-700 text-white'
                        : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                    }`}
                  >
                    {memberData?.pma_agreed && memberData?.dues_paid 
                      ? 'Pre-Order Now' 
                      : 'Complete Membership to Order'
                    }
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'locations' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
            {locations.map((location) => (
              <div key={location.id} className="bg-gray-800 rounded-lg p-4 sm:p-6">
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start mb-4 gap-2">
                  <h3 className="text-lg sm:text-xl font-bold text-white flex-1">{location.name}</h3>
                  {location.is_member_exclusive && (
                    <span className="text-xs bg-orange-600 text-white px-2 py-1 rounded w-fit">
                      MEMBERS ONLY
                    </span>
                  )}
                </div>
                <div className="space-y-2 text-sm sm:text-base">
                  <p className="text-gray-400">📍 {location.address}</p>
                  <p className="text-gray-400">📅 {location.date}</p>
                  <p className="text-gray-400">⏰ {location.start_time} - {location.end_time}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'events' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
            {events.map((event) => (
              <div key={event.id} className="bg-gray-800 rounded-lg p-4 sm:p-6">
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start mb-4 gap-2">
                  <h3 className="text-lg sm:text-xl font-bold text-white flex-1">{event.title}</h3>
                  <span className="text-xs bg-orange-600 text-white px-2 py-1 rounded w-fit">
                    {event.tier_required.toUpperCase()}
                  </span>
                </div>
                <p className="text-gray-400 mb-4 text-sm sm:text-base">{event.description}</p>
                <div className="text-gray-400 mb-4 space-y-1 text-sm sm:text-base">
                  <p>📅 {event.date} at {event.time}</p>
                  <p>📍 {event.location}</p>
                  <p>👥 {event.current_attendees}/{event.max_attendees} attendees</p>
                </div>
                <button className="w-full bg-orange-600 hover:bg-orange-700 text-white py-3 sm:py-2 rounded-lg font-medium transition-colors text-sm sm:text-base">
                  Join Event
                </button>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'orders' && (
          <div className="space-y-4">
            {orders.length === 0 ? (
              <div className="text-center text-gray-400 py-8 sm:py-12">
                <p className="text-sm sm:text-base">No orders yet. Start by ordering from the menu!</p>
              </div>
            ) : (
              orders.map((order) => (
                <div key={order.id} className="bg-gray-800 rounded-lg p-4 sm:p-6">
                  <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start mb-4 gap-3">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg sm:text-xl font-bold text-white">Order #{order.id.slice(0, 8)}</h3>
                      <p className="text-gray-400 text-sm sm:text-base break-words">
                        Pickup: {order.pickup_time} at {order.pickup_location}
                      </p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm whitespace-nowrap ${
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

        {activeTab === 'affiliates' && (
          <AffiliateDashboard />
        )}
        
        {activeTab === 'staking' && (
          <SolanaWalletProvider>
            <BBCStakingInterface />
          </SolanaWalletProvider>
        )}
      </div>
    </div>
  );
};

// Main App
function App() {
  // Combine authentication state into a single object for atomic updates
  const [authState, setAuthState] = useState({
    isAuthenticated: false,
    memberAddress: null,
    showAuth: false,
    showAdmin: false,  // Add admin panel state
    showDebug: false,  // Add debug panel state
    showStaking: false, // Add staking panel state
    showLogin: false,   // Add login page state
    registrationInProgress: false  // Add flag to prevent race conditions during registration
  });

  useEffect(() => {
    const checkAuth = () => {
      // Skip auth check if registration is in progress to prevent race conditions
      if (authState.registrationInProgress) {
        console.log('Skipping auth check - registration in progress');
        return;
      }
      
      // Skip auth check if user just became authenticated (prevent immediate override)
      if (authState.isAuthenticated && authState.memberAddress) {
        console.log('Skipping auth check - user is already authenticated');
        return;
      }
      
      const authenticated = bchAuthService.isAuthenticated();
      
      if (authenticated) {
        // Decode JWT to get address
        const token = bchAuthService.getStoredToken();
        if (token) {
          try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            // Handle both wallet auth (payload.sub) and email auth (payload.email)
            const memberAddress = payload.sub || payload.email || payload.member_id;
            
            console.log('Auth check: Setting authenticated state for:', memberAddress);
            setAuthState(prev => ({
              ...prev,
              isAuthenticated: true,
              memberAddress: memberAddress,
              showAuth: false,  // Ensure we hide auth forms when authenticated
              registrationInProgress: false  // Clear registration flag when authenticated
            }));
          } catch (e) {
            console.error('Token decode error:', e);
            // Clear potentially corrupted tokens
            localStorage.removeItem('bch_auth_token');
            localStorage.removeItem('accessToken');
            localStorage.removeItem('memberData');
            setAuthState(prev => ({
              ...prev,
              isAuthenticated: false,
              memberAddress: null,
              registrationInProgress: false
            }));
          }
        }
      }
      // Removed the else clause that was clearing auth state - this was causing the issue!
    };

    // Only run auth check on initial load, not on every state change
    if (!authState.isAuthenticated && !authState.registrationInProgress) {
      checkAuth();
    }
    
    // Check authentication less frequently
    const interval = setInterval(() => {
      if (!authState.isAuthenticated && !authState.registrationInProgress) {
        checkAuth();
      }
    }, 60000); // Reduced to once per minute
    
    return () => clearInterval(interval);
  }, []); // Empty dependency array - only run on mount

  // Add debugging function for users
  const debugAuthState = () => {
    console.log('=== BBC Authentication Debug ===');
    console.log('Auth State:', authState);
    console.log('Stored bch_auth_token:', localStorage.getItem('bch_auth_token'));
    console.log('Stored accessToken:', localStorage.getItem('accessToken'));
    console.log('Stored memberData:', localStorage.getItem('memberData'));
    console.log('bchAuthService.isAuthenticated():', bchAuthService.isAuthenticated());
    
    if (bchAuthService.getStoredToken()) {
      try {
        const token = bchAuthService.getStoredToken();
        const payload = JSON.parse(atob(token.split('.')[1]));
        console.log('Token payload:', payload);
      } catch (e) {
        console.log('Token decode error:', e);
      }
    }
    console.log('================================');
  };

  // Debug: Log the current auth state
  useEffect(() => {
    console.log('=== AUTH STATE DEBUG ===');
    console.log('isAuthenticated:', authState.isAuthenticated);
    console.log('memberAddress:', authState.memberAddress);
    console.log('showAuth:', authState.showAuth);
    console.log('showLogin:', authState.showLogin);
    console.log('registrationInProgress:', authState.registrationInProgress);
    console.log('=========================');
  }, [authState]);

  // Debug: Add button to force check auth state
  useEffect(() => {
    window.debugAuthState = () => {
      console.log('=== CURRENT AUTH STATE ===');
      console.log(authState);
      console.log('bchAuthService.isAuthenticated():', bchAuthService.isAuthenticated());
      console.log('localStorage bch_auth_token:', localStorage.getItem('bch_auth_token'));
      console.log('===========================');
    };
    console.log('Debug: Type window.debugAuthState() to check auth state');
  }, [authState]);

  const handleAuthSuccess = useCallback((address) => {
    console.log('Authentication successful for address:', address);
    // Atomic state update to prevent race conditions
    setAuthState({
      isAuthenticated: true,
      memberAddress: address,
      showAuth: false
    });
  }, []);

  const handleAuthError = (error) => {
    console.error('Auth error:', error);
  };

  // Check for admin access via URL parameter
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('admin') === 'true') {
      setAuthState(prev => ({ ...prev, showAdmin: true }));
    }
    if (urlParams.get('debug') === 'true') {
      setAuthState(prev => ({ ...prev, showDebug: true }));
    }
    if (urlParams.get('staking') === 'true') {
      setAuthState(prev => ({ ...prev, showStaking: true }));
    }
    if (urlParams.get('login') === 'true' || window.location.pathname === '/login') {
      setAuthState(prev => ({ ...prev, showLogin: true }));
    }
  }, []);

  // Use the combined state for render condition
  if (authState.showDebug) {
    return <WalletDebug />;
  }

  if (authState.showAdmin) {
    return <AdminPanel />;
  }

  // Debug: Show which component should render
  const getComponentToRender = () => {
    if (authState.showLogin) return "LoginPage";
    if (authState.showStaking) return "StakingInterface";
    if (authState.isAuthenticated && authState.memberAddress) return "MemberDashboard";
    if (authState.showAuth) return "PMAgreementPage";
    return "LandingPage";
  };

  // Debug: Log what should render
  useEffect(() => {
    const componentToRender = getComponentToRender();
    console.log(`=== RENDER LOGIC: Should render ${componentToRender} ===`);
    console.log('Conditions:');
    console.log('- showLogin:', authState.showLogin);
    console.log('- showStaking:', authState.showStaking);
    console.log('- isAuthenticated && memberAddress:', authState.isAuthenticated && authState.memberAddress);
    console.log('- showAuth:', authState.showAuth);
    console.log('==================================================');
  }, [authState]);

  if (authState.showLogin) {
    return (
      <BBCStakingProvider>
        <LoginPage 
          onLoginSuccess={(user) => {
            console.log('Login successful:', user);
            setAuthState(prev => ({ 
              ...prev, 
              isAuthenticated: true, 
              memberAddress: user.wallet_address || user.email || user.id,
              showLogin: false,
              registrationInProgress: false  // Clear any registration flag
            }));
          }}
          onBackToHome={() => {
            setAuthState(prev => ({ ...prev, showLogin: false }));
            window.history.pushState({}, '', '/');
          }}
        />
      </BBCStakingProvider>
    );
  }

  if (authState.showStaking && !authState.showLogin) {
    return (
      <BBCStakingProvider>
        <div className="min-h-screen bg-gray-900">
          <PumpTokenTicker />
          <BBCStakingInterface />
        </div>
      </BBCStakingProvider>
    );
  }

  if (authState.isAuthenticated && authState.memberAddress && !authState.showLogin && !authState.showStaking && !authState.showAuth && !authState.registrationInProgress) {
    return (
      <BBCStakingProvider>
        <MemberDashboard memberAddress={authState.memberAddress} />
      </BBCStakingProvider>
    );
  }

  if (authState.showAuth && !authState.showLogin && !authState.showStaking) {
    return (
      <BBCStakingProvider>
        <PMAgreementPage memberAddress="" onComplete={(userData) => {
          if (userData) {
            // User successfully registered - set authentication state
            setAuthState(prev => ({ 
              ...prev, 
              showAuth: false,
              isAuthenticated: true,
              memberAddress: userData.email || userData.id,
              registrationInProgress: false
            }));
          } else {
            // Registration cancelled - go back to landing page
            setAuthState(prev => ({ 
              ...prev, 
              showAuth: false,
              registrationInProgress: false 
            }));
          }
        }} />
      </BBCStakingProvider>
    );
  }

  return (
    <BBCStakingProvider>
      <LandingPage 
        onGetStarted={() => setAuthState(prev => ({ ...prev, showAuth: true }))}
        onMemberLogin={() => setAuthState(prev => ({ ...prev, showLogin: true }))}
      />
    </BBCStakingProvider>
  );
}

export default App;