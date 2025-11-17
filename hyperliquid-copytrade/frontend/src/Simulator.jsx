import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './Simulator.css'

const API_URL = 'http://127.0.0.1:8000'

function Simulator() {
  const navigate = useNavigate()

  // Multi-wallet state
  const [walletToAdd, setWalletToAdd] = useState('')
  const [wallets, setWallets] = useState([])
  const [initialBalance, setInitialBalance] = useState(10000)
  const [network, setNetwork] = useState('testnet')

  // App state
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  useEffect(() => {
    checkStatus()
    const interval = setInterval(checkStatus, 5000)
    return () => clearInterval(interval)
  }, [])

  const checkStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/status`)
      if (response.ok) {
        const data = await response.json()
        if (data.multi_wallet && data.wallets) {
          setWallets(data.wallets)
        }
      }
    } catch (err) {
      console.error('Error checking status:', err)
    }
  }

  const handleAddWallet = async () => {
    if (!walletToAdd) {
      setError('Ingresa una wallet address')
      return
    }

    if (!walletToAdd.startsWith('0x')) {
      setError('La wallet debe empezar con 0x')
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const response = await fetch(`${API_URL}/add-wallet`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          target_wallet: walletToAdd,
          testnet: network === 'testnet',
          initial_balance: initialBalance
        })
      })

      const data = await response.json()

      if (response.ok) {
        setSuccess(`Wallet añadida: ${walletToAdd.slice(0, 10)}...`)
        setWalletToAdd('')
        await checkStatus()
      } else {
        setError(data.detail || 'Error al añadir wallet')
      }
    } catch (err) {
      setError(`Error: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleRemoveWallet = async (wallet) => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/remove-wallet/${wallet}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        setSuccess(`Wallet removida: ${wallet.slice(0, 10)}...`)
        await checkStatus()
      } else {
        const data = await response.json()
        setError(data.detail || 'Error al remover wallet')
      }
    } catch (err) {
      setError(`Error: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleStopAll = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/stop-all`, {
        method: 'POST'
      })

      if (response.ok) {
        setSuccess('Todas las wallets detenidas')
        setWallets([])
        await checkStatus()
      } else {
        const data = await response.json()
        setError(data.detail || 'Error al detener wallets')
      }
    } catch (err) {
      setError(`Error: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-container">
      <button className="back-button" onClick={() => navigate('/')}>
        ← Volver
      </button>

      <div className="page-header">
        <h1 className="page-title">SIMULATOR</h1>
        <p className="page-subtitle">Testea hasta 15 wallets con dinero fake y compara traders</p>
      </div>

      {wallets.length > 0 && (
        <div className="wallets-section">
          <div className="section-header">
            <h3>🔍 Testeando {wallets.length} Wallet{wallets.length > 1 ? 's' : ''}</h3>
            <button onClick={handleStopAll} className="stop-all-button" disabled={loading}>
              Stop All
            </button>
          </div>

          <div className="traders-grid">
            {wallets
              .sort((a, b) => b.roi - a.roi)
              .map((wallet) => (
                <div key={wallet.wallet} className="trader-card">
                  {/* Header */}
                  <div className="trader-card-header">
                    <div className="trader-wallet">
                      <span className="wallet-address" title={wallet.wallet}>
                        {wallet.wallet.slice(0, 8)}...{wallet.wallet.slice(-6)}
                      </span>
                      <div className="badges-row">
                        {wallet.fee_factor_ratio !== null && wallet.fee_factor_ratio !== undefined && (
                          <span
                            className={`ffr-badge ${
                              wallet.fee_factor_ratio >= 0.8 ? 'ffr-high' :
                              wallet.fee_factor_ratio >= 0.5 ? 'ffr-medium' :
                              'ffr-low'
                            }`}
                            title={`Fee Factor (mixed): ${(wallet.fee_factor_ratio * 100).toFixed(1)}%`}
                          >
                            FFr
                          </span>
                        )}
                        {wallet.fee_factor_ratio_taker !== null && wallet.fee_factor_ratio_taker !== undefined && (
                          <span
                            className={`ffr-badge ${
                              wallet.fee_factor_ratio_taker >= 0.8 ? 'ffr-high' :
                              wallet.fee_factor_ratio_taker >= 0.5 ? 'ffr-medium' :
                              'ffr-low'
                            }`}
                            title={`Fee Factor (100% taker): ${(wallet.fee_factor_ratio_taker * 100).toFixed(1)}%`}
                          >
                            FFt
                          </span>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => handleRemoveWallet(wallet.wallet)}
                      className="card-remove-btn"
                      disabled={loading}
                      title="Remover trader"
                    >
                      ✕
                    </button>
                  </div>

                  {/* Main Stats */}
                  <div className="trader-main-stats">
                    <div className="main-stat">
                      <span className="main-stat-label">ROI</span>
                      <span className={`main-stat-value ${wallet.roi >= 0 ? 'positive' : 'negative'}`}>
                        {wallet.roi?.toFixed(2)}%
                      </span>
                    </div>
                    <div className="main-stat">
                      <span className="main-stat-label">Balance</span>
                      <span className="main-stat-value">${wallet.current_balance?.toFixed(2)}</span>
                    </div>
                  </div>

                  {/* Secondary Stats Grid */}
                  <div className="trader-stats-grid">
                    <div className="stat-box-small">
                      <span className="stat-box-label">PnL Total</span>
                      <span className={`stat-box-value ${wallet.total_pnl >= 0 ? 'positive' : 'negative'}`}>
                        ${wallet.total_pnl?.toFixed(2)}
                      </span>
                    </div>
                    <div className="stat-box-small">
                      <span className="stat-box-label">Unrealized</span>
                      <span className={`stat-box-value ${wallet.unrealized_pnl >= 0 ? 'positive' : 'negative'}`}>
                        ${wallet.unrealized_pnl?.toFixed(2)}
                      </span>
                    </div>
                    <div className="stat-box-small">
                      <span className="stat-box-label">Realized</span>
                      <span className={`stat-box-value ${(wallet.realized_pnl || 0) >= 0 ? 'positive' : 'negative'}`}>
                        ${wallet.realized_pnl?.toFixed(2)}
                      </span>
                    </div>
                    <div className="stat-box-small">
                      <span className="stat-box-label">Fees</span>
                      <span className="stat-box-value">${wallet.total_fees_paid?.toFixed(2)}</span>
                    </div>
                  </div>

                  {/* Footer */}
                  <div className="trader-card-footer">
                    <span className="trades-count">{wallet.trades_copied} trades copiados</span>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      <div className="add-wallet-card">
        <h3 className="card-title">Añadir Wallets para Testear</h3>
        <p className="card-subtitle">Puedes añadir hasta 15 wallets y compararlas en tiempo real</p>

        <div className="add-wallet-form">
          <div className="form-row">
            <div className="form-group-compact">
              <label className="form-label-small">Balance Inicial</label>
              <input
                className="form-input-compact"
                type="number"
                placeholder="10000"
                value={initialBalance}
                onChange={(e) => setInitialBalance(Number(e.target.value))}
                min="100"
                step="1000"
              />
            </div>

            <div className="form-group-compact flex-grow">
              <label className="form-label-small">Wallet Address</label>
              <input
                className="form-input-compact"
                type="text"
                placeholder="0x..."
                value={walletToAdd}
                onChange={(e) => setWalletToAdd(e.target.value)}
              />
            </div>

            <button
              onClick={handleAddWallet}
              className="add-button"
              disabled={loading || wallets.length >= 15}
            >
              {loading ? '...' : `+ Añadir (${wallets.length}/15)`}
            </button>
          </div>

          <div className="network-row">
            <label className="form-label-small">Network:</label>
            <div className="toggle-group-small">
              <button
                className={`toggle-btn-small ${network === 'testnet' ? 'active' : ''}`}
                onClick={() => setNetwork('testnet')}
              >
                Testnet
              </button>
              <button
                className={`toggle-btn-small ${network === 'mainnet' ? 'active' : ''}`}
                onClick={() => setNetwork('mainnet')}
              >
                Mainnet
              </button>
            </div>
          </div>
        </div>

        {wallets.length === 0 && (
          <div className="empty-state">
            <p>👆 Añade wallets para comenzar a testear</p>
          </div>
        )}
      </div>

      {error && (
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          <strong>Éxito:</strong> {success}
        </div>
      )}
    </div>
  )
}

export default Simulator
