import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const API_URL = 'http://127.0.0.1:8000'

function UltraCopyTrading() {
  const navigate = useNavigate()

  // Form inputs
  const [apiKey, setApiKey] = useState('')
  const [apiSecret, setApiSecret] = useState('')
  const [targetWallet, setTargetWallet] = useState('')
  const [copyRatio, setCopyRatio] = useState(1.0)
  const [useTestnet, setUseTestnet] = useState(false)

  // App state
  const [isRunning, setIsRunning] = useState(false)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  useEffect(() => {
    checkStatus()
    const interval = setInterval(checkStatus, 2000)
    return () => clearInterval(interval)
  }, [])

  const checkStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/status`)
      if (response.ok) {
        const data = await response.json()
        setIsRunning(data.is_running)
        if (data.is_running && data.stats) {
          setStats(data.stats)
        }
      }
    } catch (err) {
      // Backend not running or not responding
      setIsRunning(false)
      setStats(null)
    }
  }

  const handleStart = async () => {
    if (!apiKey || !apiSecret || !targetWallet) {
      setError('Por favor completa todos los campos requeridos')
      return
    }

    if (!targetWallet.startsWith('0x')) {
      setError('La wallet debe empezar con 0x')
      return
    }

    if (copyRatio <= 0 || copyRatio > 10) {
      setError('Copy ratio debe estar entre 0.01 y 10')
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
          copy_ratio: copyRatio,
          testnet: useTestnet
        })
      })

      const data = await response.json()

      if (response.ok) {
        setSuccess('✅ Copy trading iniciado! Esperando trades del target...')
        setIsRunning(true)
        await checkStatus()
      } else {
        setError(data.detail || 'Error al iniciar copy trading')
      }
    } catch (err) {
      setError(`Error: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleStop = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_URL}/stop`, {
        method: 'POST'
      })

      const data = await response.json()

      if (response.ok) {
        setSuccess(`✅ Copy trading detenido. ${data.stats?.trades_copied || 0} trades copiados`)
        setIsRunning(false)
        setStats(null)
      } else {
        setError(data.detail || 'Error al detener')
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
        <h1 className="page-title">⚡ ULTRA COPY TRADING</h1>
        <p className="page-subtitle">
          Copy trading en tiempo real con latencia {'<'} 100ms
        </p>
      </div>

      {/* Status Banner */}
      {isRunning && (
        <div style={{
          background: 'rgba(255, 215, 0, 0.1)',
          border: '1px solid rgba(255, 215, 0, 0.3)',
          borderRadius: '10px',
          padding: '15px',
          marginBottom: '20px'
        }}>
          <h3 style={{ color: '#FFD700', marginBottom: '10px' }}>
            ● Copy Trading Activo
          </h3>
          {stats && (
            <div style={{ fontSize: '0.9rem', color: '#ccc' }}>
              <div>Trades copiados: {stats.trades_copied}</div>
              {stats.avg_latency_ms > 0 && (
                <>
                  <div>Latencia promedio: {stats.avg_latency_ms.toFixed(1)}ms</div>
                  <div>Latencia mín/máx: {stats.min_latency_ms.toFixed(1)}ms / {stats.max_latency_ms.toFixed(1)}ms</div>
                </>
              )}
              <div>Mis posiciones: {stats.my_positions}</div>
              <div>Target posiciones: {stats.target_positions}</div>
            </div>
          )}
        </div>
      )}

      {/* Errors & Success */}
      {error && (
        <div className="error-message" style={{ marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {success && (
        <div className="success-message" style={{ marginBottom: '20px' }}>
          {success}
        </div>
      )}

      {/* Configuration Form */}
      {!isRunning && (
        <div className="form-section" style={{
          background: 'rgba(10, 10, 10, 0.95)',
          border: '1px solid rgba(255, 215, 0, 0.3)',
          borderRadius: '10px',
          padding: '30px',
          marginBottom: '20px'
        }}>
          <h3 style={{ color: '#FFD700', marginBottom: '20px' }}>
            Configuración
          </h3>

          <div className="form-group" style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', color: '#ccc' }}>
              API Key *
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Tu Hyperliquid API Key"
              style={{
                width: '100%',
                padding: '12px',
                background: 'rgba(0, 0, 0, 0.5)',
                border: '1px solid rgba(255, 215, 0, 0.3)',
                borderRadius: '5px',
                color: '#fff',
                fontSize: '0.95rem'
              }}
            />
          </div>

          <div className="form-group" style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', color: '#ccc' }}>
              API Secret *
            </label>
            <input
              type="password"
              value={apiSecret}
              onChange={(e) => setApiSecret(e.target.value)}
              placeholder="Tu Hyperliquid API Secret"
              style={{
                width: '100%',
                padding: '12px',
                background: 'rgba(0, 0, 0, 0.5)',
                border: '1px solid rgba(255, 215, 0, 0.3)',
                borderRadius: '5px',
                color: '#fff',
                fontSize: '0.95rem'
              }}
            />
          </div>

          <div className="form-group" style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', color: '#ccc' }}>
              Target Wallet *
            </label>
            <input
              type="text"
              value={targetWallet}
              onChange={(e) => setTargetWallet(e.target.value)}
              placeholder="0x..."
              style={{
                width: '100%',
                padding: '12px',
                background: 'rgba(0, 0, 0, 0.5)',
                border: '1px solid rgba(255, 215, 0, 0.3)',
                borderRadius: '5px',
                color: '#fff',
                fontSize: '0.95rem',
                fontFamily: 'monospace'
              }}
            />
          </div>

          <div className="form-group" style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '8px', color: '#ccc' }}>
              Copy Ratio: {(copyRatio * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0.1"
              max="2"
              step="0.1"
              value={copyRatio}
              onChange={(e) => setCopyRatio(parseFloat(e.target.value))}
              style={{ width: '100%' }}
            />
            <div style={{ fontSize: '0.8rem', color: '#888', marginTop: '5px' }}>
              1.0 = copias 100%, 0.5 = copias 50%, 2.0 = copias 200%
            </div>
          </div>

          <div className="form-group" style={{ marginBottom: '25px' }}>
            <label style={{ display: 'flex', alignItems: 'center', color: '#ccc', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={useTestnet}
                onChange={(e) => setUseTestnet(e.target.checked)}
                style={{ marginRight: '10px' }}
              />
              Usar Testnet (recomendado para pruebas)
            </label>
          </div>

          <button
            onClick={handleStart}
            disabled={loading}
            style={{
              width: '100%',
              padding: '15px',
              background: loading ? '#666' : 'linear-gradient(135deg, #FFD700 0%, #FFED4E 100%)',
              border: 'none',
              borderRadius: '8px',
              color: '#000',
              fontSize: '1.1rem',
              fontWeight: 'bold',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'all 0.3s'
            }}
          >
            {loading ? 'Iniciando...' : '🚀 Iniciar Copy Trading'}
          </button>
        </div>
      )}

      {/* Stop Button */}
      {isRunning && (
        <div style={{ textAlign: 'center' }}>
          <button
            onClick={handleStop}
            disabled={loading}
            style={{
              padding: '15px 40px',
              background: loading ? '#666' : 'rgba(255, 165, 0, 0.2)',
              border: '1px solid #FFA500',
              borderRadius: '8px',
              color: '#FFA500',
              fontSize: '1rem',
              fontWeight: 'bold',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Deteniendo...' : '⏹ Detener Copy Trading'}
          </button>
        </div>
      )}

      {/* Info Section */}
      <div style={{
        marginTop: '30px',
        padding: '20px',
        background: 'rgba(10, 10, 10, 0.5)',
        border: '1px solid rgba(255, 215, 0, 0.2)',
        borderRadius: '10px'
      }}>
        <h4 style={{ color: '#FFD700', marginBottom: '15px' }}>ℹ️ Información</h4>
        <ul style={{ color: '#ccc', fontSize: '0.9rem', lineHeight: '1.8' }}>
          <li>⚡ Latencia objetivo: {'<'} 100ms (evento → orden)</li>
          <li>🎯 Sistema WebSocket en tiempo real</li>
          <li>💰 Usa dinero real - empieza con testnet</li>
          <li>🔒 Tus API keys NO se guardan</li>
          <li>📊 Latencia se muestra en tiempo real</li>
          <li>⚠️ Empieza con copy ratio bajo (0.1-0.5) para probar</li>
        </ul>
      </div>
    </div>
  )
}

export default UltraCopyTrading
