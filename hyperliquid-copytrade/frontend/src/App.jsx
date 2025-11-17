import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Home from './Home'
import UltraCopyTrading from './UltraCopyTrading'
import Simulator from './Simulator'
import SimulatorV2 from './SimulatorV2'
import './index.css'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/copytrading" element={<UltraCopyTrading />} />
        <Route path="/simulator" element={<Simulator />} />
        <Route path="/simulator-v2" element={<SimulatorV2 />} />
      </Routes>
    </Router>
  )
}

export default App
