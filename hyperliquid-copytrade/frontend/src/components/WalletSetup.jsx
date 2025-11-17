import { useState, useEffect } from 'react';
import client from '../api/client';

export default function WalletSetup() {
  const [walletAddress, setWalletAddress] = useState('');
  const [currentWallet, setCurrentWallet] = useState(null);
  const [message, setMessage] = useState({ type: '', text: '' });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchAccountStatus();
  }, []);

  const fetchAccountStatus = async () => {
    try {
      const response = await client.get('/account/status');
      if (response.data.wallet_address) {
        setCurrentWallet(response.data.wallet_address);
      }
    } catch (err) {
      console.error('Failed to fetch account status:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage({ type: '', text: '' });
    setLoading(true);

    try {
      const response = await client.post('/account/set-wallet', {
        wallet_address: walletAddress,
      });

      setMessage({
        type: 'success',
        text: response.data.message,
      });
      setCurrentWallet(walletAddress);
      setWalletAddress('');
    } catch (err) {
      setMessage({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to save wallet address',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async () => {
    if (!confirm('Are you sure you want to remove this wallet?')) {
      return;
    }

    try {
      await client.delete('/account/wallet');
      setCurrentWallet(null);
      setMessage({
        type: 'success',
        text: 'Wallet removed successfully',
      });
    } catch (err) {
      setMessage({
        type: 'error',
        text: 'Failed to remove wallet',
      });
    }
  };

  return (
    <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
      <h2 className="text-2xl font-bold text-white mb-4">Connect Hyperliquid Wallet</h2>

      {currentWallet ? (
        <div className="space-y-4">
          <div className="bg-green-900/30 border border-green-500/50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400 mb-1">Connected Wallet</p>
                <p className="text-white font-mono text-sm break-all">{currentWallet}</p>
              </div>
              <button
                onClick={handleRemove}
                className="ml-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md text-sm"
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className="bg-blue-900/30 border border-blue-500/50 rounded-lg p-4 mb-6">
            <p className="text-sm text-gray-300">
              Enter your Hyperliquid wallet address to connect your account. This allows you to view
              your trading activity and set up copy trading.
            </p>
            <p className="text-xs text-gray-400 mt-2">
              Example: 0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="wallet" className="block text-sm font-medium text-gray-300 mb-2">
                Wallet Address
              </label>
              <input
                id="wallet"
                type="text"
                value={walletAddress}
                onChange={(e) => setWalletAddress(e.target.value)}
                placeholder="0x..."
                required
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-md text-white placeholder-gray-500 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {message.text && (
              <div
                className={`px-4 py-3 rounded ${
                  message.type === 'success'
                    ? 'bg-green-900/50 border border-green-500 text-green-200'
                    : 'bg-red-900/50 border border-red-500 text-red-200'
                }`}
              >
                {message.text}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Connecting...' : 'Connect Wallet'}
            </button>
          </form>
        </>
      )}
    </div>
  );
}
