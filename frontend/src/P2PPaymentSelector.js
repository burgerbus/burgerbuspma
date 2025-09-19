import React, { useState, useEffect } from 'react';
import { bchAuthService } from './BCHAuth';

const P2PPaymentSelector = ({ memberEmail, onPaymentSelected }) => {
  const [paymentMethods, setPaymentMethods] = useState({});
  const [selectedMethod, setSelectedMethod] = useState(null);
  const [paymentInstructions, setPaymentInstructions] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPaymentMethods();
  }, []);

  const loadPaymentMethods = async () => {
    try {
      const response = await bchAuthService.get('/api/payments/methods');
      setPaymentMethods(response.payment_methods);
    } catch (error) {
      console.error('Failed to load payment methods:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectPaymentMethod = async (methodKey) => {
    setSelectedMethod(methodKey);
    setLoading(true);

    try {
      const response = await bchAuthService.post('/api/payments/create-p2p-payment', null, {
        params: {
          payment_method: methodKey,
          user_email: memberEmail
        }
      });

      setPaymentInstructions(response);
      onPaymentSelected && onPaymentSelected(response);
    } catch (error) {
      console.error('Failed to create payment instructions:', error);
      alert('Failed to create payment instructions. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handlePaymentSent = () => {
    alert('Thank you! Admin will verify your payment within 24 hours and activate your membership.');
    // Could redirect to a waiting page or back to main
  };

  const copyToClipboard = (text, label) => {
    navigator.clipboard.writeText(text);
    alert(`${label} copied to clipboard!`);
  };

  if (loading && !selectedMethod) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
        <span className="ml-3 text-gray-400">Loading payment options...</span>
      </div>
    );
  }

  if (paymentInstructions) {
    return <PaymentInstructionsView 
      instructions={paymentInstructions} 
      onPaymentSent={handlePaymentSent}
      onBack={() => {
        setSelectedMethod(null);
        setPaymentInstructions(null);
      }}
      copyToClipboard={copyToClipboard}
    />;
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white mb-4">
          Complete Your FREE Membership
        </h2>
        <p className="text-gray-400 mb-2">
          Private Membership Association - No Payment Required
        </p>
        <div className="bg-green-900/20 border border-green-600 rounded-lg p-3 mb-6">
          <p className="text-green-400 text-sm">
            🎉 <strong>FREE Membership!</strong> No payment required to join the club!
          </p>
          <p className="text-green-300 text-xs mt-1">
            Bitcoin Cash payment option available for future menu purchases
          </p>
          <p className="text-green-300 text-xs mt-2 font-medium">
            Simply complete your PMA agreement to become a member
          </p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {Object.entries(paymentMethods).map(([key, method]) => (
          <PaymentMethodCard
            key={key}
            methodKey={key}
            method={method}
            onSelect={() => selectPaymentMethod(key)}
          />
        ))}
      </div>

      <div className="text-center text-gray-400 text-sm">
        <p>All payments are processed as member-to-member (P2P) transactions</p>
        <p>No merchant fees • No credit card processing • True P2P</p>
      </div>
    </div>
  );
};

const PaymentMethodCard = ({ methodKey, method, onSelect }) => {
  const getIcon = (key) => {
    switch (key) {
      case 'cashapp': return '💸';
      case 'venmo': return '💚';
      case 'zelle': return '⚡';
      case 'bch': return '₿';
      default: return '💰';
    }
  };

  const getDescription = (key) => {
    switch (key) {
      case 'cashapp': return 'Coming Soon';
      case 'venmo': return 'Coming Soon';
      case 'zelle': return 'Coming Soon';
      case 'bch': return 'Bitcoin Cash - Available for future purchases';
      default: return 'Payment option coming soon';
    }
  };

  return (
    <button
      onClick={onSelect}
      className="bg-gray-700 hover:bg-gray-600 border border-gray-600 hover:border-orange-500 rounded-lg p-6 text-left transition-all duration-200 group"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="text-3xl">{getIcon(methodKey)}</div>
        <div className="text-right">
          <div className="text-white font-bold text-lg">
            ${method.amount}
          </div>
          {method.cashstamp && (
            <div className="text-green-400 text-sm font-medium">
              +${method.cashstamp} bonus
            </div>
          )}
        </div>
      </div>
      
      <h3 className="text-white font-bold text-lg mb-1 group-hover:text-orange-400 transition-colors">
        {method.display_name}
      </h3>
      
      <p className="text-gray-400 text-sm mb-3">
        {getDescription(methodKey)}
      </p>
      
      <div className="text-orange-400 text-sm font-medium">
        Send to: {method.handle}
      </div>
      
      {methodKey === 'bch' && (
        <div className="mt-2 text-green-400 text-xs">
          🎁 Net cost: $6.00 (after $15 cashstamp)
        </div>
      )}
    </button>
  );
};

const PaymentInstructionsView = ({ instructions, onPaymentSent, onBack, copyToClipboard }) => {
  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white mb-2">
          Send Your {instructions.display_name} Payment
        </h2>
        <p className="text-gray-400">
          Member-to-Member P2P Transaction
        </p>
      </div>

      <div className="bg-gray-700 rounded-lg p-6">
        <div className="grid md:grid-cols-2 gap-6">
          {/* Payment Details */}
          <div className="space-y-4">
            <div className="bg-gray-600 rounded-lg p-4">
              <h3 className="text-white font-bold mb-3">💰 Payment Details</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-300">Method:</span>
                  <span className="text-white font-medium">{instructions.display_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Amount:</span>
                  <span className="text-orange-400 font-bold">${instructions.amount}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Send to:</span>
                  <span className="text-orange-400 font-mono">{instructions.handle}</span>
                </div>
                {instructions.cashstamp_bonus > 0 && (
                  <div className="flex justify-between">
                    <span className="text-gray-300">Bonus:</span>
                    <span className="text-green-400 font-bold">+${instructions.cashstamp_bonus} BCH</span>
                  </div>
                )}
              </div>
            </div>

            <div className="bg-gray-600 rounded-lg p-4">
              <h3 className="text-white font-bold mb-3">📝 Instructions</h3>
              <p className="text-gray-300 text-sm mb-3">
                {instructions.instructions}
              </p>
              
              <div className="bg-yellow-900/20 border border-yellow-600 rounded-lg p-3 mb-4">
                <p className="text-yellow-400 font-bold text-sm">
                  ⚠️ IMPORTANT: Include your email address in the payment memo/note
                </p>
                <p className="text-yellow-300 text-xs mt-1">
                  This helps us verify your payment and activate your membership quickly
                </p>
              </div>
              
              <div className="space-y-2">
                <button
                  onClick={() => copyToClipboard(instructions.handle, 'Payment handle')}
                  className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm transition-colors"
                >
                  📋 Copy {instructions.display_name} Handle
                </button>
                
                <button
                  onClick={() => copyToClipboard(instructions.amount.toString(), 'Amount')}
                  className="w-full px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded text-sm transition-colors"
                >
                  💰 Copy Amount (${instructions.amount})
                </button>

                <button
                  onClick={() => copyToClipboard(instructions.user_email || 'your-email@example.com', 'Your Email')}
                  className="w-full px-3 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded text-sm transition-colors"
                >
                  📧 Copy Your Email (for memo)
                </button>
              </div>
            </div>
          </div>

          {/* QR Code for BCH */}
          {instructions.qr_code && (
            <div className="text-center">
              <h3 className="text-white font-bold mb-3">📱 QR Code Payment</h3>
              <div className="bg-white rounded-lg p-4 inline-block">
                <img
                  src={instructions.qr_code}
                  alt="Payment QR Code"
                  className="w-48 h-48"
                />
              </div>
              <p className="text-gray-400 text-sm mt-2">
                Scan with your BCH wallet
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="flex gap-4">
        <button
          onClick={onBack}
          className="flex-1 px-6 py-3 bg-gray-600 hover:bg-gray-500 text-white rounded-lg font-medium transition-colors"
        >
          ← Back to Payment Options
        </button>
        
        <button
          onClick={onPaymentSent}
          className="flex-1 px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors"
        >
          ✅ I've Sent the Payment
        </button>
      </div>

      <div className="bg-yellow-900/20 border border-yellow-600 rounded-lg p-4 text-center">
        <p className="text-yellow-400 font-medium">⏰ Payment will be verified within 24 hours</p>
        <p className="text-gray-300 text-sm mt-1">
          You'll receive confirmation once your membership is activated
        </p>
      </div>
    </div>
  );
};

export default P2PPaymentSelector;