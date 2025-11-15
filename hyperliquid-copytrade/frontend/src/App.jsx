import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Home from './Home'
import CopyTrading from './CopyTrading'
import Simulator from './Simulator'
import './index.css'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/copytrading" element={<CopyTrading />} />
        <Route path="/simulator" element={<Simulator />} />
      </Routes>
    </Router>
  )
}

export default App
