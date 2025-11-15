import { useState, useEffect } from 'react'

const API_URL = 'http://127.0.0.1:8000'

function App() {
  // Form inputs
  const [apiKey, setApiKey] = useState('')
  const [apiSecret, setApiSecret] = useState('')
  const [targetWallet, setTargetWallet] = useState('')
  const [network, setNetwork] = useState('testnet')

  // Paper trading
  const [paperMode, setPaperMode] = useState(true) // Default to paper mode for safety
  const [initialBalance, setInitialBalance] = useState(10000)

  // App state
  const [isRunning, setIsRunning] = useState(false)
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  // Theme selection
  const [theme, setTheme] = useState('purple') // purple, dark, minimal, green, blue

  // Check status on mount and every 5 seconds
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
        setIsRunning(data.active || false)
      }
    } catch (err) {
      console.error('Error checking status:', err)
    }
  }

  const handleStart = async () => {
    // Validation
    if (!targetWallet) {
      setError('Por favor ingresa la Target Wallet')
      return
    }

    if (!targetWallet.startsWith('0x')) {
      setError('Target Wallet debe comenzar con 0x')
      return
    }

    // Real trading requires API credentials
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
          testnet: network === 'testnet',
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

  const themes = {
    purple: { name: '🟣 Purple', icon: '🎨' },
    dark: { name: '⚫ Dark', icon: '🌙' },
    minimal: { name: '⚪ Minimal', icon: '✨' },
    green: { name: '🟢 Matrix', icon: '💰' },
    blue: { name: '🔵 Ocean', icon: '🌊' }
  }

  return (
    <div className={`app-wrapper theme-${theme}`}>
      <div className="container">
        <div className="header">
          <h1>Hyperliquid CopyTrading</h1>
          <p>Copia trades automáticamente usando % de margen</p>
        </div>

        {/* Running Indicator */}
        {isRunning && status && (
          <div>
            <div className="running-indicator">
              <div className="pulse"></div>
              <div className="running-info">
                <h3>{status.paper_mode ? 'Paper Trading Activo' : 'CopyTrading Real Activo'}</h3>
                <p>Target: {status.target_wallet?.slice(0, 10)}...</p>
                <p>Trades: {status.trades_copied}</p>
              </div>
            </div>

            {/* Paper Trading Stats Dashboard */}
            {status.paper_mode && (
              <div className="paper-stats">
                <h3>📊 Estadísticas</h3>
                <div className="stats-grid">
                  <div className="stat-box">
                    <span className="stat-label">Balance</span>
                    <span className="stat-value">${status.current_balance?.toFixed(2)}</span>
                  </div>
                  <div className="stat-box">
                    <span className="stat-label">PnL Total</span>
                    <span className={`stat-value ${status.total_pnl >= 0 ? 'positive' : 'negative'}`}>
                      ${status.total_pnl?.toFixed(2)}
                    </span>
                  </div>
                  <div className="stat-box">
                    <span className="stat-label">ROI</span>
                    <span className={`stat-value ${status.roi >= 0 ? 'positive' : 'negative'}`}>
                      {status.roi?.toFixed(2)}%
                    </span>
                  </div>
                  <div className="stat-box">
                    <span className="stat-label">Fees Pagadas</span>
                    <span className="stat-value">${status.total_fees_paid?.toFixed(2)}</span>
                  </div>
                </div>
                {status.open_positions > 0 && (
                  <div className="positions-info">
                    <p><strong>Posiciones abiertas:</strong> {status.open_positions}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Form */}
        {!isRunning ? (
          <div>
            {/* Paper / Real Toggle */}
            <div className="form-group">
              <label>Modo de Trading</label>
              <div className="network-selector">
                <button
                  className={`network-btn ${paperMode ? 'active' : ''}`}
                  onClick={() => setPaperMode(true)}
                >
                  📝 Paper (Sin riesgo)
                </button>
                <button
                  className={`network-btn ${!paperMode ? 'active' : ''}`}
                  onClick={() => setPaperMode(false)}
                >
                  💰 Real
                </button>
              </div>
            </div>

            {/* Paper Trading Initial Balance */}
            {paperMode && (
              <div className="form-group">
                <label>Balance Inicial (Paper)</label>
                <input
                  type="number"
                  placeholder="10000"
                  value={initialBalance}
                  onChange={(e) => setInitialBalance(Number(e.target.value))}
                  min="100"
                  step="100"
                />
              </div>
            )}

            {/* API Credentials (only for real trading) */}
            {!paperMode && (
              <>
                <div className="form-group">
                  <label>API Key</label>
                  <input
                    type="text"
                    placeholder="Tu Hyperliquid API Key"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>API Secret (Private Key)</label>
                  <input
                    type="password"
                    placeholder="0x..."
                    value={apiSecret}
                    onChange={(e) => setApiSecret(e.target.value)}
                  />
                </div>
              </>
            )}

            <div className="form-group">
              <label>Target Wallet</label>
              <input
                type="text"
                placeholder="0x... (wallet del trader a copiar)"
                value={targetWallet}
                onChange={(e) => setTargetWallet(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Network</label>
              <div className="network-selector">
                <button
                  className={`network-btn ${network === 'testnet' ? 'active' : ''}`}
                  onClick={() => setNetwork('testnet')}
                >
                  Testnet
                </button>
                <button
                  className={`network-btn ${network === 'mainnet' ? 'active' : ''}`}
                  onClick={() => setNetwork('mainnet')}
                >
                  Mainnet
                </button>
              </div>
            </div>

            <button
              className="btn btn-primary"
              onClick={handleStart}
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="loading"></span> Iniciando...
                </>
              ) : (
                'Start CopyTrading'
              )}
            </button>
          </div>
        ) : (
          <button
            className="btn btn-danger"
            onClick={handleStop}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="loading"></span> Deteniendo...
              </>
            ) : (
              'Stop CopyTrading'
            )}
          </button>
        )}

        {/* Status Messages */}
        {error && (
          <div className="status-box error">
            <strong>Error:</strong> {error}
          </div>
        )}

        {success && (
          <div className="status-box success">
            <strong>Éxito:</strong> {success}
          </div>
        )}

        {/* Info Box */}
        {!isRunning && !error && !success && (
          <div className="status-box warning">
            <strong>⚠️ Importante:</strong>
            <ul style={{ marginTop: '8px', marginLeft: '20px' }}>
              <li>Comienza siempre en Testnet</li>
              <li>API Key solo con permisos de trading (NO withdraw)</li>
              <li>El bot copia % de margen usado, no el tamaño nominal</li>
            </ul>
          </div>
        )}

        {/* Theme Selector */}
        <div className="theme-selector">
          <p className="theme-label">Elige tu tema:</p>
          <div className="theme-buttons">
            {Object.keys(themes).map((themeName) => (
              <button
                key={themeName}
                className={`theme-btn ${theme === themeName ? 'active' : ''}`}
                onClick={() => setTheme(themeName)}
                title={themes[themeName].name}
              >
                <span className="theme-icon">{themes[themeName].icon}</span>
                <span className="theme-name">{themes[themeName].name}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
