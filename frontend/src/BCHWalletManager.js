// Bitcoin Cash Wallet Connection Manager
import BitcoreLibCash from 'bitcore-lib-cash';

class BCHWalletManager {
    constructor() {
        this.connectedWallet = null;
        this.availableWallets = [];
        this.eventListeners = new Map();
    }

    // Detect available Bitcoin Cash wallets
    async detectWallets() {
        const wallets = [];
        
        // Check for Edge Wallet (popular BCH wallet)
        if (window.edgeProvider) {
            wallets.push({
                name: 'Edge Wallet',
                type: 'extension',
                instance: window.edgeProvider
            });
        }
        
        // Check for Bitcoin.com Wallet
        if (window.bitcoincom) {
            wallets.push({
                name: 'Bitcoin.com',
                type: 'extension',
                instance: window.bitcoincom
            });
        }
        
        // Check for Badger Wallet
        if (window.badger) {
            wallets.push({
                name: 'Badger Wallet',
                type: 'extension',
                instance: window.badger
            });
        }

        // Check for generic Bitcoin Cash wallet
        if (window.bitcoincash) {
            wallets.push({
                name: 'Bitcoin Cash Wallet',
                type: 'extension',
                instance: window.bitcoincash
            });
        }

        // Check for web3-like BCH providers
        if (window.bch) {
            wallets.push({
                name: 'BCH Web3 Wallet',
                type: 'extension',
                instance: window.bch
            });
        }

        // Mobile wallet detection through user agent
        if (this.isMobileDevice()) {
            wallets.push({
                name: 'Mobile BCH Wallet',
                type: 'mobile',
                instance: null
            });
        }

        // If no wallets detected, add a demo wallet for testing
        if (wallets.length === 0) {
            wallets.push({
                name: 'Demo BCH Wallet',
                type: 'demo',
                instance: null
            });
        }

        this.availableWallets = wallets;
        return wallets;
    }

    // Connect to specific wallet
    async connectWallet(walletName) {
        const wallet = this.availableWallets.find(w => w.name === walletName);
        if (!wallet) {
            throw new Error(`Wallet ${walletName} not available`);
        }

        try {
            switch (wallet.type) {
                case 'extension':
                    return await this.connectExtensionWallet(wallet);
                case 'mobile':
                    return await this.connectMobileWallet(wallet);
                case 'demo':
                    return await this.connectDemoWallet(wallet);
                default:
                    throw new Error(`Unsupported wallet type: ${wallet.type}`);
            }
        } catch (error) {
            console.error(`Failed to connect to ${walletName}:`, error);
            throw error;
        }
    }

    // Connect to browser extension wallet
    async connectExtensionWallet(wallet) {
        try {
            let accounts = [];
            
            // Handle different wallet APIs
            if (wallet.name === 'Edge Wallet' && wallet.instance) {
                // Edge wallet specific connection
                try {
                    await wallet.instance.enable();
                    accounts = await wallet.instance.getAccounts();
                } catch (error) {
                    // Try alternative Edge wallet methods
                    if (wallet.instance.requestAccounts) {
                        accounts = await wallet.instance.requestAccounts();
                    } else if (wallet.instance.enable) {
                        await wallet.instance.enable();
                        accounts = wallet.instance.accounts || [];
                    }
                }
            } else if (wallet.instance && wallet.instance.getAccounts) {
                // Standard BCH wallet API
                accounts = await wallet.instance.getAccounts();
            } else if (wallet.instance && wallet.instance.requestAccounts) {
                // Web3-style API
                accounts = await wallet.instance.requestAccounts();
            } else {
                throw new Error(`Wallet ${wallet.name} API not supported`);
            }
            
            if (!accounts || accounts.length === 0) {
                throw new Error('No accounts available in wallet or user denied access');
            }

            // Get the first account
            const address = Array.isArray(accounts) ? accounts[0] : accounts;

            this.connectedWallet = {
                name: wallet.name,
                type: wallet.type,
                address: address,
                instance: wallet.instance
            };

            this.emit('walletConnected', this.connectedWallet);
            return this.connectedWallet;
            
        } catch (error) {
            console.error(`Extension wallet connection failed for ${wallet.name}:`, error);
            throw new Error(`${wallet.name} connection failed: ${error.message}`);
        }
    }

    // Handle mobile wallet connection through deep linking
    async connectMobileWallet(wallet) {
        return new Promise((resolve, reject) => {
            // Generate connection request
            const connectionRequest = {
                type: 'connection_request',
                timestamp: Date.now(),
                origin: window.location.origin
            };

            // Create deep link for mobile wallet
            const deepLink = this.createMobileWalletLink(connectionRequest);
            
            // Open mobile wallet
            window.location.href = deepLink;
            
            // Set up timeout for connection response
            const timeout = setTimeout(() => {
                reject(new Error('Mobile wallet connection timeout'));
            }, 30000);

            // Listen for connection response
            const handleResponse = (event) => {
                if (event.data.type === 'wallet_connected') {
                    clearTimeout(timeout);
                    window.removeEventListener('message', handleResponse);
                    
                    this.connectedWallet = {
                        name: wallet.name,
                        type: wallet.type,
                        address: event.data.address,
                        instance: null
                    };
                    
                    resolve(this.connectedWallet);
                }
            };

            window.addEventListener('message', handleResponse);
        });
    }

    // Connect to demo wallet for testing
    async connectDemoWallet(wallet) {
        // Generate a demo Bitcoin Cash address for testing
        const demoAddress = "bitcoincash:qph0duvh0zn0r2um7znh8gx20p50dr3ycc5lcp0sc4";
        
        this.connectedWallet = {
            name: wallet.name,
            type: wallet.type,
            address: demoAddress,
            instance: null
        };

        this.emit('walletConnected', this.connectedWallet);
        return this.connectedWallet;
    }

    // Sign message with connected wallet
    async signMessage(message) {
        if (!this.connectedWallet) {
            throw new Error('No wallet connected');
        }

        try {
            switch (this.connectedWallet.type) {
                case 'extension':
                    return await this.signWithExtension(message);
                case 'mobile':
                    return await this.signWithMobile(message);
                case 'demo':
                    return await this.signWithDemo(message);
                default:
                    throw new Error('Unsupported wallet type for signing');
            }
        } catch (error) {
            console.error('Message signing failed:', error);
            throw error;
        }
    }

    // Sign message using extension wallet
    async signWithExtension(message) {
        try {
            let signature;
            
            // Handle different wallet signing APIs
            if (this.connectedWallet.name === 'Edge Wallet' && this.connectedWallet.instance) {
                // Edge wallet specific signing
                try {
                    signature = await this.connectedWallet.instance.signMessage(
                        this.connectedWallet.address,
                        message
                    );
                } catch (error) {
                    // Try alternative Edge signing methods
                    if (this.connectedWallet.instance.sign) {
                        signature = await this.connectedWallet.instance.sign(message);
                    } else if (this.connectedWallet.instance.personal && this.connectedWallet.instance.personal.sign) {
                        signature = await this.connectedWallet.instance.personal.sign(message, this.connectedWallet.address);
                    }
                }
            } else if (this.connectedWallet.instance.signMessage) {
                // Standard BCH wallet signing
                signature = await this.connectedWallet.instance.signMessage(
                    this.connectedWallet.address,
                    message
                );
            } else if (this.connectedWallet.instance.sign) {
                // Alternative signing method
                signature = await this.connectedWallet.instance.sign(message);
            } else {
                throw new Error(`Wallet ${this.connectedWallet.name} does not support message signing`);
            }
            
            return {
                address: this.connectedWallet.address,
                signature: signature,
                message: message
            };
            
        } catch (error) {
            console.error(`Extension signing failed for ${this.connectedWallet.name}:`, error);
            throw new Error(`${this.connectedWallet.name} signing failed: ${error.message}`);
        }
    }

    // Handle mobile wallet message signing
    async signWithMobile(message) {
        return new Promise((resolve, reject) => {
            const signingRequest = {
                type: 'sign_request',
                message: message,
                address: this.connectedWallet.address,
                timestamp: Date.now()
            };

            // Create deep link for signing request
            const signingLink = this.createMobileWalletLink(signingRequest);
            window.location.href = signingLink;

            // Set up timeout
            const timeout = setTimeout(() => {
                reject(new Error('Mobile wallet signing timeout'));
            }, 60000);

            // Listen for signing response
            const handleSigningResponse = (event) => {
                if (event.data.type === 'message_signed') {
                    clearTimeout(timeout);
                    window.removeEventListener('message', handleSigningResponse);
                    
                    resolve({
                        address: event.data.address,
                        signature: event.data.signature,
                        message: message
                    });
                }
            };

            window.addEventListener('message', handleSigningResponse);
        });
    }

    // Demo wallet signing for testing
    async signWithDemo(message) {
        // Generate a demo signature for testing
        const demoSignature = `demo_signature_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        
        return {
            address: this.connectedWallet.address,
            signature: demoSignature,
            message: message
        };
    }

    // Utility methods
    isMobileDevice() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
            navigator.userAgent
        );
    }

    createMobileWalletLink(request) {
        const encodedRequest = encodeURIComponent(JSON.stringify(request));
        return `bitcoincash://wallet?request=${encodedRequest}`;
    }

    // Event management
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }

    emit(event, data) {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            listeners.forEach(callback => callback(data));
        }
    }

    // Disconnect wallet
    disconnect() {
        if (this.connectedWallet) {
            this.emit('walletDisconnected', this.connectedWallet);
            this.connectedWallet = null;
        }
    }

    // Get connected wallet info
    getWalletInfo() {
        return this.connectedWallet;
    }

    // Check if wallet is connected
    isConnected() {
        return !!this.connectedWallet;
    }
}

export default BCHWalletManager;