import React, { useState, useEffect } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AdminPanel = ({ onLogout, adminUser }) => {
  const [pendingPayments, setPendingPayments] = useState([]);
  const [affiliatePayouts, setAffiliatePayouts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState({});
  const [activeTab, setActiveTab] = useState('payments');

  useEffect(() => {
    loadData();
    // Refresh every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const [paymentsResponse, affiliatesResponse] = await Promise.all([
        fetch(`${BACKEND_URL}/api/admin/pending-payments`, {
          headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
        }).then(r => r.json()),
        fetch(`${BACKEND_URL}/api/admin/affiliate-payouts`, {
          headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
        }).then(r => r.json())
      ]);
      
      setPendingPayments(paymentsResponse.pending_payments || []);
      setAffiliatePayouts(affiliatesResponse.pending_payouts || []);
    } catch (error) {
      console.error('Failed to load admin data:', error);
    } finally {
      setLoading(false);
    }
  };

  const verifyPayment = async (paymentId, transactionId) => {
    if (!transactionId.trim()) {
      alert('Please enter a transaction ID');
      return;
    }

    setVerifying(prev => ({ ...prev, [paymentId]: true }));

    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${BACKEND_URL}/api/admin/verify-payment?payment_id=${paymentId}&transaction_id=${transactionId.trim()}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();

      if (data.success) {
        alert('Payment verified successfully! Member activated.');
        loadData(); // Refresh the data
      }
    } catch (error) {
      console.error('Verification failed:', error);
      alert(`Verification failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setVerifying(prev => ({ ...prev, [paymentId]: false }));
    }
  };

  const sendCashstamp = async (paymentId, recipientAddress) => {
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${BACKEND_URL}/api/admin/send-cashstamp?payment_id=${paymentId}&recipient_address=${recipientAddress}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      const data = await response.json();

      if (data.success) {
        const instructions = data.instructions;
        const message = `
Send Cashstamp Instructions:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

From: ${instructions.from_address}
To: ${instructions.to_address}
Amount: ${instructions.amount_bch} BCH ($${data.cashstamp_amount_usd})
Memo: ${instructions.memo}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Please send this amount manually from your admin wallet.
        `;
        
        alert(message);
        
        // Copy recipient address to clipboard
        navigator.clipboard.writeText(instructions.to_address);
      }
    } catch (error) {
      console.error('Cashstamp generation failed:', error);
      alert(`Cashstamp failed: ${error.response?.data?.detail || error.message}`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading admin panel...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="bg-gray-800 rounded-lg p-8">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold text-white">
                🔐 Bitcoin Ben's Admin Panel
              </h1>
              {adminUser && (
                <p className="text-gray-400 text-sm mt-1">
                  Logged in as: {adminUser.email}
                </p>
              )}
            </div>
            <div className="flex gap-2">
              <button
                onClick={loadData}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                🔄 Refresh
              </button>
              <button
                onClick={onLogout}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
              >
                🚪 Logout
              </button>
            </div>
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-bold text-white mb-4">
              💰 Pending Payments ({pendingPayments.length})
            </h2>
            
            {pendingPayments.length === 0 ? (
              <div className="bg-gray-700 rounded-lg p-6 text-center">
                <p className="text-gray-400">No pending payments found</p>
              </div>
            ) : (
              <div className="space-y-4">
                {pendingPayments.map((payment) => (
                  <PaymentCard
                    key={payment.payment_id}
                    payment={payment}
                    onVerify={verifyPayment}
                    onSendCashstamp={sendCashstamp}
                    isVerifying={verifying[payment.payment_id]}
                  />
                ))}
              </div>
            )}
          </div>

          <div className="bg-yellow-900/20 border border-yellow-600 rounded-lg p-4">
            <h3 className="text-yellow-400 font-bold mb-2">📋 Admin Instructions:</h3>
            <ul className="text-gray-300 text-sm space-y-1">
              <li>1. Check your BCH wallet for incoming $21 payments</li>
              <li>2. Copy the transaction ID from your wallet</li>
              <li>3. Paste it into the verification form and click "Verify Payment"</li>
              <li>4. Send the $18 BCH cashstamp to the member's address</li>
              <li>5. $3 goes to affiliate (or treasury if no referral)</li>
              <li>6. Member will be automatically activated after verification</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

const PaymentCard = ({ payment, onVerify, onSendCashstamp, isVerifying }) => {
  const [transactionId, setTransactionId] = useState('');
  const [expanded, setExpanded] = useState(false);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const copyToClipboard = (text, label) => {
    navigator.clipboard.writeText(text);
    alert(`${label} copied to clipboard!`);
  };

  return (
    <div className="bg-gray-700 rounded-lg p-6">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-white font-bold text-lg">
            Payment #{payment.payment_id.slice(-8)}
          </h3>
          <p className="text-gray-400 text-sm">
            Created: {formatDate(payment.created_at)}
          </p>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-orange-400 hover:text-orange-300 transition-colors"
        >
          {expanded ? '▼' : '▶'} Details
        </button>
      </div>

      <div className="grid md:grid-cols-3 gap-4 mb-4">
        <div className="bg-gray-600 rounded p-3">
          <div className="text-gray-300 text-sm">Amount</div>
          <div className="text-white font-bold">
            ${payment.amount_usd} ({payment.amount_bch.toFixed(8)} BCH)
          </div>
        </div>
        <div className="bg-gray-600 rounded p-3">
          <div className="text-gray-300 text-sm">User Address</div>
          <div className="text-orange-400 font-mono text-sm">
            {payment.user_address.slice(0, 20)}...
          </div>
        </div>
        <div className="bg-gray-600 rounded p-3">
          <div className="text-gray-300 text-sm">Expires</div>
          <div className="text-white text-sm">
            {formatDate(payment.expires_at)}
          </div>
        </div>
      </div>

      {expanded && (
        <div className="space-y-4 mb-4">
          <div className="bg-gray-600 rounded p-3">
            <div className="text-gray-300 text-sm mb-2">Full Payment ID:</div>
            <div className="flex items-center gap-2">
              <code className="text-orange-400 text-sm bg-gray-800 px-2 py-1 rounded flex-1">
                {payment.payment_id}
              </code>
              <button
                onClick={() => copyToClipboard(payment.payment_id, 'Payment ID')}
                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
              >
                Copy
              </button>
            </div>
          </div>

          <div className="bg-gray-600 rounded p-3">
            <div className="text-gray-300 text-sm mb-2">User BCH Address:</div>
            <div className="flex items-center gap-2">
              <code className="text-orange-400 text-sm bg-gray-800 px-2 py-1 rounded flex-1">
                {payment.user_address}
              </code>
              <button
                onClick={() => copyToClipboard(payment.user_address, 'User Address')}
                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
              >
                Copy
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-3">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Enter BCH transaction ID to verify payment..."
            value={transactionId}
            onChange={(e) => setTransactionId(e.target.value)}
            className="flex-1 px-3 py-2 bg-gray-600 text-white rounded border border-gray-500 focus:border-orange-500 focus:outline-none text-sm"
          />
          <button
            onClick={() => onVerify(payment.payment_id, transactionId)}
            disabled={isVerifying || !transactionId.trim()}
            className="px-6 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded font-medium transition-colors"
          >
            {isVerifying ? '⏳' : '✅'} Verify
          </button>
        </div>

        <button
          onClick={() => onSendCashstamp(payment.payment_id, payment.user_address)}
          className="w-full px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded font-medium transition-colors"
        >
          💰 Generate $15 Cashstamp Instructions
        </button>
      </div>
    </div>
  );
};

export default AdminPanel;