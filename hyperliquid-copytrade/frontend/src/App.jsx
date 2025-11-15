import { useState, useEffect } from 'react'

const API_URL = 'http://127.0.0.1:8000'

function App() {
  // Form inputs
  const [apiKey, setApiKey] = useState('')
  const [apiSecret, setApiSecret] = useState('')
  const [targetWallet, setTargetWallet] = useState('')
  const [network, setNetwork] = useState('testnet') // 'testnet' or 'mainnet'

  // App state
  const [isRunning, setIsRunning] = useState(false)
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

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
    if (!apiKey || !apiSecret || !targetWallet) {
      setError('Por favor completa todos los campos')
      return
    }

    if (!apiSecret.startsWith('0x')) {
      setError('API Secret debe comenzar con 0x')
      return
    }

    if (!targetWallet.startsWith('0x')) {
      setError('Target Wallet debe comenzar con 0x')
      return
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
          testnet: network === 'testnet'
        })
      })

      const data = await response.json()

      if (response.ok) {
        setIsRunning(true)
        setSuccess('CopyTrading iniciado correctamente!')
        await checkStatus()
      } else {
        setError(data.detail || data.message || 'Error al iniciar CopyTrading')
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
    <div className="container">
      <div className="header">
        <h1>Hyperliquid CopyTrading</h1>
        <p>Copia trades automáticamente usando % de margen</p>
      </div>

      {/* Running Indicator */}
      {isRunning && status && (
        <div className="running-indicator">
          <div className="pulse"></div>
          <div className="running-info">
            <h3>CopyTrading Activo</h3>
            <p>Target: {status.target_wallet?.slice(0, 10)}...</p>
            <p>Network: {status.testnet ? 'Testnet' : 'Mainnet'}</p>
            {status.trades_copied !== undefined && (
              <p>Trades copiados: {status.trades_copied}</p>
            )}
          </div>
        </div>
      )}

      {/* Form */}
      {!isRunning ? (
        <div>
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
    </div>
  )
}

export default App
