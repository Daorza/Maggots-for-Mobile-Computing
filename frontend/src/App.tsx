import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Login from './pages/Login';
import Connect from './pages/Connect';
import Dashboard from './pages/Dashboard';
import Monitoring from './pages/Monitoring';
import InputData from './pages/InputData';
import AIAnalysis from './pages/AIAnalysis';
import Laporan from './pages/Laporan';
import Edukasi from './pages/Edukasi';
import Settings from './pages/Settings';
// Trigger Vite Reload

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/connect" element={<Connect />} />
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="monitoring" element={<Monitoring />} />
          <Route path="input" element={<InputData />} />
          <Route path="ai" element={<AIAnalysis />} />
          <Route path="laporan" element={<Laporan />} />
          <Route path="edukasi" element={<Edukasi />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
