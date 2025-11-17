import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import WalletSetup from '../components/WalletSetup';
import client from '../api/client';

export default function Dashboard() {
  const [user, setUser] = useState(null);
  const [accountStatus, setAccountStatus] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadUserData();
    fetchAccountStatus();
  }, []);

  const loadUserData = () => {
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
  };

  const fetchAccountStatus = async () => {
    try {
      const response = await client.get('/account/status');
      setAccountStatus(response.data);
    } catch (err) {
      console.error('Failed to fetch account status:', err);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      {/* Header */}
      <nav className="bg-gray-900/80 backdrop-blur-sm border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-white">
                Hyperliquid Copy Trading
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-400 text-sm">{user?.email}</span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-md text-sm"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Account Status Card */}
          <div className="lg:col-span-1">
            <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
              <h2 className="text-lg font-semibold text-white mb-4">Account Status</h2>
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-400">Email</p>
                  <p className="text-white">{user?.email}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Account Type</p>
                  <p className="text-white">
                    {accountStatus?.user?.testnet_mode ? 'Testnet' : 'Mainnet'}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Hyperliquid Connection</p>
                  <div className="flex items-center mt-1">
                    <div
                      className={`w-2 h-2 rounded-full mr-2 ${
                        accountStatus?.hyperliquid_connected
                          ? 'bg-green-500'
                          : 'bg-red-500'
                      }`}
                    />
                    <span className="text-white">
                      {accountStatus?.hyperliquid_connected ? 'Connected' : 'Not Connected'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Wallet Setup Card */}
          <div className="lg:col-span-2">
            <WalletSetup />
          </div>
        </div>

        {/* Coming Soon Section */}
        {accountStatus?.hyperliquid_connected && (
          <div className="mt-6">
            <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
              <h2 className="text-xl font-semibold text-white mb-4">Copy Trading</h2>
              <div className="bg-blue-900/30 border border-blue-500/50 rounded-lg p-6 text-center">
                <p className="text-gray-300 mb-2">Coming Soon!</p>
                <p className="text-sm text-gray-400">
                  Copy trading functionality will be available soon. You'll be able to:
                </p>
                <ul className="text-sm text-gray-400 mt-3 space-y-1 text-left max-w-md mx-auto">
                  <li>• Follow successful traders automatically</li>
                  <li>• Copy trades in real-time via WebSocket</li>
                  <li>• Scale positions based on your account size</li>
                  <li>• Track performance and manage risk</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
