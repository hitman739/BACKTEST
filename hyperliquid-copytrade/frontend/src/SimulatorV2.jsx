import { useState, useEffect, useRef } from 'react'
import './Home.css'

const API_BASE = 'http://localhost:8000'
const WS_URL = 'ws://localhost:8000/ws'

function SimulatorV2() {
  const [wallets, setWallets] = useState([])
  const [newWallet, setNewWallet] = useState('')
  const [initialBalance, setInitialBalance] = useState(10000)
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef(null)

  // =====================
  // WEBSOCKET CONNECTION
  // =====================

  useEffect(() => {
    connectWebSocket()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const connectWebSocket = () => {
    const ws = new WebSocket(WS_URL)

    ws.onopen = () => {
      console.log('✅ WebSocket connected')
      setIsConnected(true)
    }

    ws.onclose = () => {
      console.log('❌ WebSocket disconnected')
      setIsConnected(false)

      // Reconnect after 3 seconds
      setTimeout(connectWebSocket, 3000)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.type === 'metrics_update') {
        // Update wallets with new metrics
        setWallets(prevWallets => {
          const updatedWallets = [...prevWallets]

          data.data.forEach(update => {
            const index = updatedWallets.findIndex(w => w.wallet === update.wallet)

            if (index !== -1) {
              updatedWallets[index] = {
                ...updatedWallets[index],
                ...update.metrics
              }
            }
          })

          return updatedWallets
        })
      }
    }

    wsRef.current = ws
  }

  // =====================
  // LOAD INITIAL DATA
  // =====================

  useEffect(() => {
    loadWallets()
  }, [])

  const loadWallets = async () => {
    try {
      const response = await fetch(`${API_BASE}/status`)
      const data = await response.json()

      setWallets(data.wallets.map(w => ({
        wallet: w.wallet,
        equity: w.equity || 0,
        total_pnl: w.total_pnl || 0,
        roi: w.roi || 0,
        num_trades: w.num_trades || 0,
        num_open_positions: w.num_open_positions || 0,
        fee_factor_mixed: w.fee_factor_mixed,
        fee_factor_taker: w.fee_factor_taker
      })))
    } catch (error) {
      console.error('Error loading wallets:', error)
    }
  }

  // =====================
  // WALLET OPERATIONS
  // =====================

  const handleAddWallet = async () => {
    if (!newWallet.startsWith('0x') || newWallet.length !== 42) {
      alert('Invalid wallet address')
      return
    }

    try {
      const response = await fetch(`${API_BASE}/wallet/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          wallet_address: newWallet,
          initial_balance: initialBalance
        })
      })

      if (response.ok) {
        const data = await response.json()
        console.log('Wallet added:', data)

        // Add to UI immediately (metrics will update via WebSocket)
        setWallets(prev => [...prev, {
          wallet: newWallet.toLowerCase(),
          equity: initialBalance,
          total_pnl: 0,
          roi: 0,
          num_trades: 0,
          num_open_positions: 0,
          fee_factor_mixed: null,
          fee_factor_taker: null
        }])

        setNewWallet('')
      } else {
        const error = await response.json()
        alert(`Error: ${error.detail}`)
      }
    } catch (error) {
      console.error('Error adding wallet:', error)
      alert('Failed to add wallet')
    }
  }

  const handleRemoveWallet = async (wallet) => {
    if (!confirm(`Remove ${wallet}?`)) return

    try {
      const response = await fetch(`${API_BASE}/wallet/${wallet}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        setWallets(prev => prev.filter(w => w.wallet !== wallet))
      }
    } catch (error) {
      console.error('Error removing wallet:', error)
    }
  }

  // =====================
  // FEE FACTOR BADGE
  // =====================

  const getFeeBadgeLevel = (feeFactor) => {
    if (!feeFactor) return 'unknown'
    if (feeFactor >= 0.9) return 'excellent'
    if (feeFactor >= 0.8) return 'good'
    if (feeFactor >= 0.7) return 'average'
    if (feeFactor >= 0.6) return 'poor'
    return 'terrible'
  }

  const getFeeBadgeColor = (level) => {
    const colors = {
      'excellent': '#00ff88',
      'good': '#00ccff',
      'average': '#ffaa00',
      'poor': '#ff6600',
      'terrible': '#ff3366',
      'unknown': '#666666'
    }
    return colors[level] || '#666666'
  }

  // =====================
  // RENDER
  // =====================

  return (
    <div className="home-container">
      <div className="home-header">
        <h1 className="home-title">
          📊 Simulator V2 - Real-Time WebSocket
        </h1>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          fontSize: '0.9rem'
        }}>
          <span style={{
            color: isConnected ? '#00ff88' : '#ff3366',
            fontWeight: 'bold'
          }}>
            {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </span>
          <span style={{ color: '#888' }}>
            Updates every 1 second via WebSocket
          </span>
        </div>
      </div>

      {/* Add Wallet Form */}
      <div className="simulator-controls" style={{
        background: 'rgba(10, 10, 10, 0.95)',
        border: '1px solid rgba(255, 215, 0, 0.3)',
        borderRadius: '10px',
        padding: '20px',
        marginBottom: '20px'
      }}>
        <h3 style={{ color: '#FFD700', marginBottom: '15px' }}>Add Wallet to Track</h3>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="0x..."
            value={newWallet}
            onChange={(e) => setNewWallet(e.target.value)}
            style={{
              flex: '1',
              minWidth: '300px',
              padding: '10px',
              background: 'rgba(0, 0, 0, 0.5)',
              border: '1px solid rgba(255, 215, 0, 0.3)',
              borderRadius: '5px',
              color: '#fff'
            }}
          />

          <input
            type="number"
            value={initialBalance}
            onChange={(e) => setInitialBalance(Number(e.target.value))}
            style={{
              width: '150px',
              padding: '10px',
              background: 'rgba(0, 0, 0, 0.5)',
              border: '1px solid rgba(255, 215, 0, 0.3)',
              borderRadius: '5px',
              color: '#fff'
            }}
          />

          <button
            onClick={handleAddWallet}
            style={{
              padding: '10px 20px',
              background: 'linear-gradient(135deg, #FFD700 0%, #FFED4E 100%)',
              border: 'none',
              borderRadius: '5px',
              color: '#000',
              fontWeight: 'bold',
              cursor: 'pointer'
            }}
          >
            Add Wallet
          </button>
        </div>
      </div>

      {/* Wallets Grid */}
      <div className="traders-grid">
        {wallets.map((wallet) => (
          <div key={wallet.wallet} className="trader-card" style={{
            background: 'rgba(10, 10, 10, 0.95)',
            border: '1px solid rgba(255, 215, 0, 0.3)',
            borderRadius: '10px',
            padding: '20px'
          }}>
            {/* Wallet Address */}
            <div style={{
              fontSize: '0.85rem',
              color: '#FFD700',
              marginBottom: '10px',
              fontFamily: 'monospace'
            }}>
              {wallet.wallet.slice(0, 8)}...{wallet.wallet.slice(-6)}
            </div>

            {/* Fee Factor Badges */}
            {wallet.fee_factor_mixed !== null && (
              <div style={{ display: 'flex', gap: '5px', marginBottom: '15px' }}>
                <span style={{
                  padding: '4px 8px',
                  borderRadius: '5px',
                  fontSize: '0.75rem',
                  fontWeight: 'bold',
                  background: getFeeBadgeColor(getFeeBadgeLevel(wallet.fee_factor_mixed)),
                  color: '#000'
                }}>
                  FFr: {(wallet.fee_factor_mixed * 100).toFixed(1)}%
                </span>

                <span style={{
                  padding: '4px 8px',
                  borderRadius: '5px',
                  fontSize: '0.75rem',
                  fontWeight: 'bold',
                  background: getFeeBadgeColor(getFeeBadgeLevel(wallet.fee_factor_taker)),
                  color: '#000'
                }}>
                  FFt: {(wallet.fee_factor_taker * 100).toFixed(1)}%
                </span>
              </div>
            )}

            {/* Metrics */}
            <div className="stat-row">
              <span>Equity:</span>
              <span style={{ color: '#FFD700' }}>${wallet.equity.toFixed(2)}</span>
            </div>

            <div className="stat-row">
              <span>PnL:</span>
              <span style={{ color: wallet.total_pnl >= 0 ? '#00ff88' : '#ff3366' }}>
                ${wallet.total_pnl.toFixed(2)}
              </span>
            </div>

            <div className="stat-row">
              <span>ROI:</span>
              <span style={{ color: wallet.roi >= 0 ? '#00ff88' : '#ff3366' }}>
                {wallet.roi.toFixed(2)}%
              </span>
            </div>

            <div className="stat-row">
              <span>Trades:</span>
              <span>{wallet.num_trades}</span>
            </div>

            <div className="stat-row">
              <span>Open Positions:</span>
              <span>{wallet.num_open_positions}</span>
            </div>

            {/* Remove Button */}
            <button
              onClick={() => handleRemoveWallet(wallet.wallet)}
              style={{
                width: '100%',
                marginTop: '15px',
                padding: '8px',
                background: 'rgba(255, 51, 102, 0.2)',
                border: '1px solid #ff3366',
                borderRadius: '5px',
                color: '#ff3366',
                cursor: 'pointer'
              }}
            >
              Remove
            </button>
          </div>
        ))}
      </div>

      {wallets.length === 0 && (
        <div style={{
          textAlign: 'center',
          padding: '40px',
          color: '#888'
        }}>
          No wallets tracked yet. Add one above to get started!
        </div>
      )}
    </div>
  )
}

export default SimulatorV2
