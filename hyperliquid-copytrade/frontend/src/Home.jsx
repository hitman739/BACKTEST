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
          <h2 className="module-title">COPY TRADING</h2>
          <p className="module-description">Real trading with live accounts</p>
        </div>

        <div
          className="module module-simulator"
          onClick={() => navigate('/simulator')}
        >
          <div className="module-icon">🎯</div>
          <h2 className="module-title">SIMULATOR</h2>
          <p className="module-description">Test wallets with paper money</p>
        </div>
      </div>

      <div className="home-footer">
        <p>Powered by Hyperliquid SDK</p>
      </div>
    </div>
  )
}

export default Home
