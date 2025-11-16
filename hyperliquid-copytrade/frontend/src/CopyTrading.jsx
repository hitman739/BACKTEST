import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const API_URL = 'http://127.0.0.1:8000'

function CopyTrading() {
  const navigate = useNavigate()

  // Form inputs
  const [apiKey, setApiKey] = useState('')
  const [apiSecret, setApiSecret] = useState('')
  const [targetWallet, setTargetWallet] = useState('')

  // Paper trading
  const [paperMode, setPaperMode] = useState(true)
  const [initialBalance, setInitialBalance] = useState(10000)

  // App state
  const [isRunning, setIsRunning] = useState(false)
  const [status, setStatus] = useState(null)
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
        setStatus(data)
        // Only show running if NOT multi-wallet mode
        if (!data.multi_wallet) {
          setIsRunning(data.active || false)
        }
      }
    } catch (err) {
      console.error('Error checking status:', err)
    }
  }

  const handleStart = async () => {
    if (!targetWallet) {
      setError('Por favor ingresa la Target Wallet')
      return
    }

    if (!targetWallet.startsWith('0x')) {
      setError('Target Wallet debe comenzar con 0x')
      return
    }

    if (!paperMode) {
      if (!apiKey || !apiSecret) {
        setError('API Key y Secret son requeridos para trading real')
        return
      }

      if (!apiSecret.startsWith('0x')) {
        setError('API Secret debe comenzar con 0x')
        return
      }
    }

    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const response = await fetch(`${API_URL}/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          api_key: apiKey,
          api_secret: apiSecret,
          target_wallet: targetWallet,
          testnet: false,  // Siempre mainnet
          paper_mode: paperMode,
          initial_balance: initialBalance
        })
      })

      const data = await response.json()

      if (response.ok) {
        setIsRunning(true)
        if (paperMode) {
          setSuccess(`Paper Trading iniciado con $${initialBalance.toLocaleString()}!`)
        } else {
          setSuccess('CopyTrading Real iniciado!')
        }
        await checkStatus()
      } else {
        setError(data.detail || data.message || 'Error al iniciar')
      }
    } catch (err) {
      setError(`Error de conexión: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleStop = async () => {
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const response = await fetch(`${API_URL}/stop`, {
        method: 'POST',
      })

      const data = await response.json()

      if (response.ok) {
        setIsRunning(false)
        setSuccess('CopyTrading detenido correctamente')
        await checkStatus()
      } else {
        setError(data.detail || data.message || 'Error al detener CopyTrading')
      }
    } catch (err) {
      setError(`Error de conexión: ${err.message}`)
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
        <h1 className="page-title">COPY TRADING</h1>
        <p className="page-subtitle">Copia trades automáticamente usando % de margen</p>
      </div>

      {isRunning && status && !status.multi_wallet && (
        <div className="running-card">
          <div className="pulse-indicator"></div>
          <div className="running-content">
            <h3>{status.paper_mode ? 'Paper Trading Activo' : 'CopyTrading Real Activo'}</h3>
            <p>Target: {status.target_wallet?.slice(0, 10)}...</p>
            <p>Trades: {status.trades_copied}</p>
          </div>

          {status.paper_mode && (
            <div className="stats-dashboard">
              <div className="stat-item">
                <span className="stat-label">Balance</span>
                <span className="stat-value">${status.current_balance?.toFixed(2)}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">PnL Total</span>
                <span className={`stat-value ${status.total_pnl >= 0 ? 'positive' : 'negative'}`}>
                  ${status.total_pnl?.toFixed(2)}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Unrealized</span>
                <span className={`stat-value ${(status.unrealized_pnl || 0) >= 0 ? 'positive' : 'negative'}`}>
                  ${(status.unrealized_pnl || 0)?.toFixed(2)}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Realized</span>
                <span className={`stat-value ${(status.realized_pnl || 0) >= 0 ? 'positive' : 'negative'}`}>
                  ${(status.realized_pnl || 0)?.toFixed(2)}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">ROI</span>
                <span className={`stat-value ${status.roi >= 0 ? 'positive' : 'negative'}`}>
                  {status.roi?.toFixed(2)}%
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Fees</span>
                <span className="stat-value">${status.total_fees_paid?.toFixed(2)}</span>
              </div>
            </div>
          )}
        </div>
      )}

      {!isRunning ? (
        <div className="form-card">
          <div className="form-section">
            <label className="form-label">Modo de Trading</label>
            <div className="toggle-group">
              <button
                className={`toggle-btn ${paperMode ? 'active' : ''}`}
                onClick={() => setPaperMode(true)}
              >
                📝 Paper (Sin riesgo)
              </button>
              <button
                className={`toggle-btn ${!paperMode ? 'active' : ''}`}
                onClick={() => setPaperMode(false)}
              >
                💰 Real
              </button>
            </div>
          </div>

          {paperMode && (
            <div className="form-section">
              <label className="form-label">Balance Inicial (Paper)</label>
              <input
                className="form-input"
                type="number"
                placeholder="10000"
                value={initialBalance}
                onChange={(e) => setInitialBalance(Number(e.target.value))}
                min="100"
                step="100"
              />
            </div>
          )}

          {!paperMode && (
            <>
              <div className="form-section">
                <label className="form-label">API Key</label>
                <input
                  className="form-input"
                  type="text"
                  placeholder="Tu Hyperliquid API Key"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                />
              </div>

              <div className="form-section">
                <label className="form-label">API Secret (Private Key)</label>
                <input
                  className="form-input"
                  type="password"
                  placeholder="0x..."
                  value={apiSecret}
                  onChange={(e) => setApiSecret(e.target.value)}
                />
              </div>
            </>
          )}

          <div className="form-section">
            <label className="form-label">Target Wallet</label>
            <input
              className="form-input"
              type="text"
              placeholder="0x... (wallet del trader a copiar)"
              value={targetWallet}
              onChange={(e) => setTargetWallet(e.target.value)}
            />
          </div>

          <button className="start-button" onClick={handleStart} disabled={loading}>
            {loading ? 'Iniciando...' : 'Start CopyTrading'}
          </button>
        </div>
      ) : (
        <button className="stop-button" onClick={handleStop} disabled={loading}>
          {loading ? 'Deteniendo...' : 'Stop CopyTrading'}
        </button>
      )}

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

      {!isRunning && !error && !success && (
        <div className="alert alert-warning">
          <strong>⚠️ Importante:</strong>
          <ul>
            <li>API Key solo con permisos de trading (NO withdraw)</li>
            <li>El bot copia % de margen usado, no el tamaño nominal</li>
            <li>Usa Paper Mode primero para probar sin riesgo</li>
          </ul>
        </div>
      )}
    </div>
  )
}

export default CopyTrading
