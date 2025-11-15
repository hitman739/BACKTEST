import { useState, useEffect, useRef } from 'react'

function App() {
  // Form state
  const [apiKey, setApiKey] = useState('')
  const [apiSecret, setApiSecret] = useState('')
  const [targetWallet, setTargetWallet] = useState('')
  const [testnet, setTestnet] = useState(true)

  // App state
  const [isConnected, setIsConnected] = useState(false)
  const [isCopying, setIsCopying] = useState(false)
  const [trades, setTrades] = useState([])
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')

  // WebSocket
  const ws = useRef(null)

  const API_URL = 'http://localhost:8000'

  // Connect to WebSocket
  useEffect(() => {
    connectWebSocket()

    return () => {
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [])

  const connectWebSocket = () => {
    ws.current = new WebSocket('ws://localhost:8000/ws')

    ws.current.onopen = () => {
      console.log('WebSocket connected')
      setIsConnected(true)
    }

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleWebSocketMessage(data)
    }

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error)
      setError('WebSocket connection error')
    }

    ws.current.onclose = () => {
      console.log('WebSocket disconnected')
      setIsConnected(false)
      // Reconnect after 3 seconds
      setTimeout(connectWebSocket, 3000)
    }
  }

  const handleWebSocketMessage = (data) => {
    console.log('WebSocket message:', data)

    if (data.type === 'status') {
      setStatus(data.message || `Status: ${data.status}`)
      if (data.status === 'started') {
        setIsCopying(true)
      } else if (data.status === 'stopped') {
        setIsCopying(false)
      }
    } else if (data.type === 'trade') {
      addTrade(data)
    } else if (data.type === 'error') {
      setError(data.message)
    } else if (data.type === 'info') {
      setStatus(data.message)
    }
  }

  const addTrade = (trade) => {
    const timestamp = new Date().toLocaleTimeString()
    const tradeEntry = {
      ...trade,
      timestamp
    }
    setTrades(prev => [tradeEntry, ...prev].slice(0, 50)) // Keep last 50 trades
  }

  const handleStartCopy = async () => {
    if (!apiKey || !apiSecret || !targetWallet) {
      setError('Please fill in all fields')
      return
    }

    setError('')
    setStatus('Starting copy trading...')

    try {
      const response = await fetch(`${API_URL}/start-copy`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          api_key: apiKey,
          api_secret: apiSecret,
          target_wallet: targetWallet,
          testnet: testnet
        })
      })

      const data = await response.json()

      if (response.ok) {
        setIsCopying(true)
        setStatus(`Started copying ${targetWallet}`)
      } else {
        setError(data.detail || 'Failed to start copy trading')
      }
    } catch (err) {
      setError(`Error: ${err.message}`)
    }
  }

  const handleStopCopy = async () => {
    setStatus('Stopping copy trading...')

    try {
      const response = await fetch(`${API_URL}/stop-copy`, {
        method: 'POST',
      })

      const data = await response.json()

      if (response.ok) {
        setIsCopying(false)
        setStatus('Copy trading stopped')
      } else {
        setError(data.detail || 'Failed to stop copy trading')
      }
    } catch (err) {
      setError(`Error: ${err.message}`)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Hyperliquid CopyTrade</h1>
          <p className="text-purple-100">Copy successful traders automatically</p>
          <div className="mt-2 flex items-center justify-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
            <span className="text-sm text-purple-100">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        {/* Main Card */}
        <div className="bg-white rounded-lg shadow-2xl p-8">
          {/* Form */}
          {!isCopying ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Key
                </label>
                <input
                  type="text"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="Your Hyperliquid API Key"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Secret (Private Key)
                </label>
                <input
                  type="password"
                  value={apiSecret}
                  onChange={(e) => setApiSecret(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="0x..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Target Wallet Address
                </label>
                <input
                  type="text"
                  value={targetWallet}
                  onChange={(e) => setTargetWallet(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="0x..."
                />
              </div>

              <div className="flex items-center justify-between">
                <label className="block text-sm font-medium text-gray-700">
                  Network
                </label>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setTestnet(true)}
                    className={`px-4 py-2 rounded-lg font-medium transition ${
                      testnet
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    Testnet
                  </button>
                  <button
                    onClick={() => setTestnet(false)}
                    className={`px-4 py-2 rounded-lg font-medium transition ${
                      !testnet
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    Mainnet
                  </button>
                </div>
              </div>

              <button
                onClick={handleStartCopy}
                disabled={!isConnected}
                className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white py-3 px-6 rounded-lg font-semibold hover:from-purple-700 hover:to-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isConnected ? 'Start Copy Trading' : 'Connecting...'}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-green-800">Copy Trading Active</p>
                    <p className="text-xs text-green-600 mt-1">Monitoring: {targetWallet.slice(0, 10)}...</p>
                    <p className="text-xs text-green-600">Network: {testnet ? 'Testnet' : 'Mainnet'}</p>
                  </div>
                  <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                </div>
              </div>

              <button
                onClick={handleStopCopy}
                className="w-full bg-red-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-red-700 transition"
              >
                Stop Copy Trading
              </button>
            </div>
          )}

          {/* Status & Error Messages */}
          {status && (
            <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-sm text-blue-800">{status}</p>
            </div>
          )}

          {error && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Trade Feed */}
          {trades.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Recent Trades</h3>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {trades.map((trade, index) => (
                  <div
                    key={index}
                    className="bg-gray-50 rounded-lg p-3 border border-gray-200"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2 py-1 rounded text-xs font-medium ${
                            trade.action === 'opened' || trade.is_buy
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {trade.action?.toUpperCase() || (trade.is_buy ? 'BUY' : 'SELL')}
                        </span>
                        <span className="font-medium text-gray-800">{trade.coin}</span>
                      </div>
                      <span className="text-xs text-gray-500">{trade.timestamp}</span>
                    </div>
                    <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-gray-500">Size:</span>{' '}
                        <span className="font-medium">{Math.abs(trade.size).toFixed(4)}</span>
                      </div>
                      {trade.margin_pct && (
                        <div>
                          <span className="text-gray-500">Margin:</span>{' '}
                          <span className="font-medium">{trade.margin_pct.toFixed(2)}%</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center mt-6 text-purple-100 text-sm">
          <p>⚠️ Always start with testnet to verify everything works correctly</p>
        </div>
      </div>
    </div>
  )
}

export default App
