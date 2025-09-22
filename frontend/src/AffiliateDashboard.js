import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AffiliateDashboard = () => {
  const [affiliateStats, setAffiliateStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadAffiliateStats();
  }, []);

  const loadAffiliateStats = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${BACKEND_URL}/api/affiliate/my-stats`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      const stats = await response.json();
      setAffiliateStats(stats);
    } catch (error) {
      console.error('Failed to load affiliate stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyReferralCode = () => {
    navigator.clipboard.writeText(affiliateStats.referral_code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const copyReferralLink = () => {
    const referralLink = `${window.location.origin}?ref=${affiliateStats.referral_code}`;
    navigator.clipboard.writeText(referralLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded mb-4"></div>
          <div className="h-4 bg-gray-700 rounded mb-2"></div>
          <div className="h-4 bg-gray-700 rounded w-3/4"></div>
        </div>
      </div>
    );
  }

  if (!affiliateStats) {
    return (
      <div className="bg-red-900/20 border border-red-600 rounded-lg p-6">
        <p className="text-red-400">Failed to load affiliate statistics</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white mb-2">
          💰 Your Affiliate Dashboard
        </h2>
        <p className="text-gray-400">
          Earn ${affiliateStats.commission_per_referral} for every new member you refer!
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid md:grid-cols-4 gap-4">
        <div className="bg-gray-700 rounded-lg p-6 text-center">
          <div className="text-3xl font-bold text-yellow-400">
            {affiliateStats.total_referrals}
          </div>
          <div className="text-gray-300 text-sm">Total Referrals</div>
        </div>
        
        <div className="bg-gray-700 rounded-lg p-6 text-center">
          <div className="text-3xl font-bold text-green-400">
            ${affiliateStats.total_commissions_earned.toFixed(2)}
          </div>
          <div className="text-gray-300 text-sm">Total Earned</div>
        </div>
        
        <div className="bg-gray-700 rounded-lg p-6 text-center">
          <div className="text-3xl font-bold text-orange-400">
            ${affiliateStats.unpaid_commissions.toFixed(2)}
          </div>
          <div className="text-gray-300 text-sm">Pending Payout</div>
        </div>
        
        <div className="bg-gray-700 rounded-lg p-6 text-center">
          <div className="text-3xl font-bold text-blue-400">
            ${affiliateStats.commission_per_referral}
          </div>
          <div className="text-gray-300 text-sm">Per Referral</div>
        </div>
      </div>

      {/* Referral Code Section */}
      <div className="bg-gray-700 rounded-lg p-6">
        <h3 className="text-xl font-bold text-white mb-4">📋 Your Referral Code</h3>
        
        <div className="bg-gray-800 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between">
            <code className="text-yellow-400 text-lg font-mono">
              {affiliateStats.referral_code}
            </code>
            <button
              onClick={copyReferralCode}
              className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-black rounded-lg transition-colors"
            >
              {copied ? '✅ Copied!' : '📋 Copy Code'}
            </button>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <button
            onClick={copyReferralLink}
            className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
          >
            📧 Copy Referral Link
          </button>
          
          <div className="flex gap-2">
            <button
              onClick={() => {
                const text = `Join Bitcoin Ben's Burger Bus Club PMA! Use my referral code ${affiliateStats.referral_code} and I'll earn a commission. You'll get $15 BCH cashstamp! ${window.location.origin}?ref=${affiliateStats.referral_code}`;
                navigator.clipboard.writeText(text);
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
              }}
              className="flex-1 px-4 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors text-sm"
            >
              📱 Copy Social Media Post
            </button>
          </div>
        </div>
      </div>

      {/* How It Works */}
      <div className="bg-gray-700 rounded-lg p-6">
        <h3 className="text-xl font-bold text-white mb-4">💡 How Affiliate Earnings Work</h3>
        
        <div className="space-y-4">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-yellow-600 rounded-full flex items-center justify-center text-black font-bold text-sm">
              1
            </div>
            <div>
              <p className="text-white font-medium">Share Your Code</p>
              <p className="text-gray-400 text-sm">Give friends your referral code or link</p>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-yellow-600 rounded-full flex items-center justify-center text-black font-bold text-sm">
              2
            </div>
            <div>
              <p className="text-white font-medium">They Join & Pay</p>
              <p className="text-gray-400 text-sm">New member pays $21 membership dues</p>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-yellow-600 rounded-full flex items-center justify-center text-black font-bold text-sm">
              3
            </div>
            <div>
              <p className="text-white font-medium">You Earn $3</p>
              <p className="text-gray-400 text-sm">Admin sends your commission via P2P payment</p>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-yellow-600 rounded-full flex items-center justify-center text-black font-bold text-sm">
              4
            </div>
            <div>
              <p className="text-white font-medium">They Get $15 BCH</p>
              <p className="text-gray-400 text-sm">New member receives BCH cashstamp bonus</p>
            </div>
          </div>
        </div>
      </div>

      {/* Earnings Breakdown */}
      {affiliateStats.unpaid_commissions > 0 && (
        <div className="bg-green-900/20 border border-green-600 rounded-lg p-6">
          <h3 className="text-green-400 font-bold mb-2">💰 Pending Payout</h3>
          <p className="text-white">
            You have <strong>${affiliateStats.unpaid_commissions.toFixed(2)}</strong> in pending commissions.
          </p>
          <p className="text-gray-300 text-sm mt-2">
            Admin will process affiliate payouts regularly via the same P2P methods used for membership.
          </p>
        </div>
      )}

      {/* Referral Tips */}
      <div className="bg-blue-900/20 border border-blue-600 rounded-lg p-6">
        <h3 className="text-blue-400 font-bold mb-3">🚀 Referral Tips</h3>
        <ul className="space-y-2 text-gray-300 text-sm">
          <li>• Share on crypto and Bitcoin community forums</li>
          <li>• Post on social media with your referral link</li>
          <li>• Tell friends about the $15 BCH cashstamp bonus</li>
          <li>• Mention exclusive Bitcoin burger club benefits</li>
          <li>• Emphasize P2P payments and PMA structure</li>
        </ul>
      </div>
    </div>
  );
};

export default AffiliateDashboard;