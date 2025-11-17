import { useNavigate } from 'react-router-dom'
import './Home.css'

function Home() {
  const navigate = useNavigate()

  return (
    <div className="home-container">
      <div className="home-header">
        <h1 className="home-title">HYPERLIQUID COPY TRADING</h1>
        <p className="home-subtitle">Choose your mode</p>
      </div>

      <div className="modules-container">
        <div
          className="module module-copytrading"
          onClick={() => navigate('/copytrading')}
        >
          <div className="module-icon">⚡</div>
          <h2 className="module-title">ULTRA COPY TRADING</h2>
          <p className="module-description">Real trading with {'<'}100ms latency</p>
          <div style={{ fontSize: '0.8rem', color: '#888', marginTop: '10px' }}>
            Requires: ./start_ultra.sh
          </div>
        </div>

        <div
          className="module module-simulator"
          onClick={() => navigate('/simulator')}
        >
          <div className="module-icon">📊</div>
          <h2 className="module-title">SIMULATOR</h2>
          <p className="module-description">Test multiple wallets with fake money</p>
          <div style={{ fontSize: '0.8rem', color: '#888', marginTop: '10px' }}>
            Requires: ./start_v2.sh
          </div>
        </div>
      </div>

      <div className="home-footer">
        <p>Powered by Hyperliquid SDK</p>
      </div>
    </div>
  )
}

export default Home
