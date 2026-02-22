import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Alerts from './pages/Alerts'
import SARWorkspace from './pages/SARWorkspace'
import History from './pages/History'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="alerts" element={<Alerts />} />
        <Route path="sar/:alertId" element={<SARWorkspace />} />
        <Route path="history" element={<History />} />
      </Route>
    </Routes>
  )
}

export default App
