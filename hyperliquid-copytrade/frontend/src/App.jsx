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

  // Multi-wallet testing
  const [multiWalletMode, setMultiWalletMode] = useState(false)
  const [walletToAdd, setWalletToAdd] = useState('')
  const [wallets, setWallets] = useState([]) // List of wallets being tested

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

        // Update wallets list if multi-wallet mode
        if (data.multi_wallet && data.wallets) {
          setWallets(data.wallets)
          setMultiWalletMode(true)
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
        setMultiWalletMode(true)
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

        // If no more wallets, exit multi-wallet mode
        if (wallets.length <= 1) {
          setMultiWalletMode(false)
          setWallets([])
        }
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
        setMultiWalletMode(false)
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

        {/* Multi-Wallet Testing Mode */}
        {multiWalletMode && wallets.length > 0 && (
          <div>
            <div className="running-indicator">
              <div className="pulse"></div>
              <div className="running-info">
                <h3>🔍 Testeando {wallets.length} Wallet{wallets.length > 1 ? 's' : ''}</h3>
                <p>Comparando performance en tiempo real</p>
              </div>
            </div>

            {/* Wallets Comparison Table */}
            <div className="wallets-table-container">
              <div className="table-header">
                <h3>📊 Comparación de Traders</h3>
                <button onClick={handleStopAll} className="btn btn-danger btn-small">
                  Stop All
                </button>
              </div>

              <div className="wallets-table">
                <table>
                  <thead>
                    <tr>
                      <th>Wallet</th>
                      <th>Balance</th>
                      <th>PnL</th>
                      <th>ROI</th>
                      <th>Fees</th>
                      <th>Trades</th>
                      <th>Acción</th>
                    </tr>
                  </thead>
                  <tbody>
                    {wallets
                      .sort((a, b) => b.roi - a.roi) // Sort by ROI descending
                      .map((wallet) => (
                        <tr key={wallet.wallet}>
                          <td className="wallet-cell" title={wallet.wallet}>
                            {wallet.wallet.slice(0, 6)}...{wallet.wallet.slice(-4)}
                          </td>
                          <td>${wallet.current_balance?.toFixed(2)}</td>
                          <td className={wallet.total_pnl >= 0 ? 'positive' : 'negative'}>
                            ${wallet.total_pnl?.toFixed(2)}
                          </td>
                          <td className={wallet.roi >= 0 ? 'positive-bold' : 'negative-bold'}>
                            {wallet.roi?.toFixed(2)}%
                          </td>
                          <td>${wallet.total_fees_paid?.toFixed(2)}</td>
                          <td>{wallet.trades_copied}</td>
                          <td>
                            <button
                              onClick={() => handleRemoveWallet(wallet.wallet)}
                              className="btn-remove"
                              disabled={loading}
                            >
                              ✕
                            </button>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Single Wallet Mode (original) */}
        {!multiWalletMode && isRunning && status && (
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
        {!isRunning && !multiWalletMode ? (
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

            {/* Multi-Wallet Toggle (only for paper mode) */}
            {paperMode && (
              <div className="form-group">
                <label>¿Cuántas wallets quieres testear?</label>
                <div className="network-selector">
                  <button
                    className={`network-btn ${!multiWalletMode ? 'active' : ''}`}
                    onClick={() => setMultiWalletMode(false)}
                  >
                    1 Wallet
                  </button>
                  <button
                    className={`network-btn ${multiWalletMode ? 'active' : ''}`}
                    onClick={() => setMultiWalletMode(true)}
                  >
                    🔍 Múltiples (hasta 15)
                  </button>
                </div>
              </div>
            )}

            {/* Paper Trading Initial Balance */}
            {paperMode && !multiWalletMode && (
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
        ) : !multiWalletMode && (
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

        {/* Multi-Wallet Add Form */}
        {multiWalletMode && (
          <div className="multi-wallet-form">
            <h3>🔍 Añadir Wallets para Testear</h3>
            <p className="subtitle">Puedes añadir hasta 15 wallets y compararlas en tiempo real</p>

            <div className="add-wallet-row">
              <div className="form-group-inline">
                <label>Balance Inicial</label>
                <input
                  type="number"
                  placeholder="10000"
                  value={initialBalance}
                  onChange={(e) => setInitialBalance(Number(e.target.value))}
                  min="100"
                  step="1000"
                  className="balance-input"
                />
              </div>

              <div className="form-group-inline flex-grow">
                <label>Wallet Address</label>
                <input
                  type="text"
                  placeholder="0x..."
                  value={walletToAdd}
                  onChange={(e) => setWalletToAdd(e.target.value)}
                  className="wallet-input"
                />
              </div>

              <button
                onClick={handleAddWallet}
                className="btn btn-primary btn-add"
                disabled={loading || wallets.length >= 15}
              >
                {loading ? '...' : `+ Añadir (${wallets.length}/15)`}
              </button>
            </div>

            <div className="network-selector-inline">
              <label>Network:</label>
              <button
                className={`network-btn-small ${network === 'testnet' ? 'active' : ''}`}
                onClick={() => setNetwork('testnet')}
              >
                Testnet
              </button>
              <button
                className={`network-btn-small ${network === 'mainnet' ? 'active' : ''}`}
                onClick={() => setNetwork('mainnet')}
              >
                Mainnet
              </button>
            </div>

            {wallets.length === 0 && (
              <div className="empty-state">
                <p>👆 Añade wallets para comenzar a testear</p>
              </div>
            )}
          </div>
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
