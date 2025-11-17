import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Home from './Home'
import CopyTrading from './CopyTrading'
import SimulatorV2 from './SimulatorV2'
import './index.css'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/copytrading" element={<CopyTrading />} />
        <Route path="/simulator" element={<SimulatorV2 />} />
      </Routes>
    </Router>
  )
}

export default App
