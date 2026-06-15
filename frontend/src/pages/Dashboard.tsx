import { useEffect, useState } from 'react';
import { ThermometerSun, Droplets, Scale, TrendingUp, AlertTriangle, CheckCircle, Bell, Wifi, WifiOff } from 'lucide-react';
import { LineChart, Line, ResponsiveContainer, YAxis, XAxis, CartesianGrid, Tooltip } from 'recharts';
import api from '../api';

export default function Dashboard() {
  const [metrics, setMetrics] = useState<any>(null);
  const [deviceStatus, setDeviceStatus] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [chartData, setChartData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [isEditingPhase, setIsEditingPhase] = useState(false);
  const [selectedPhase, setSelectedPhase] = useState('');
  const [isUpdatingPhase, setIsUpdatingPhase] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);

  const fetchData = async () => {
    try {
      const [metricsRes, statusRes, alertsRes, chartRes] = await Promise.all([
        api.get('/dashboard/metrics'),
        api.get('/dashboard/status'),
        api.get('/alerts/unread'),
        api.get('/dashboard/monitoring')
      ]);
      setMetrics(metricsRes.data);
      setDeviceStatus(statusRes.data);
      
      // Handle new alerts for toast (basic implementation)
      if (alertsRes.data.alerts.length > alerts.length && alerts.length > 0) {
        // Here we could trigger a toast library, for now we just update state
      }
      setAlerts(alertsRes.data.alerts);
      setChartData(chartRes.data.data);
    } catch (err) {
      console.error("Dashboard fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const markAlertsRead = async () => {
    await api.post('/alerts/mark-read');
    setAlerts([]);
  };

  const handleUpdatePhase = async () => {
    setIsUpdatingPhase(true);
    try {
      const isAuto = selectedPhase === 'Auto';
      await api.post('/dashboard/settings', {
        phase_override_enabled: isAuto ? 0 : 1,
        manual_phase: isAuto ? '' : selectedPhase
      });
      setIsEditingPhase(false);
      fetchData(); // Refresh to get new phase immediately
    } catch (err) {
      console.error("Failed to update phase", err);
    } finally {
      setIsUpdatingPhase(false);
    }
  };

  const handleReconnect = async () => {
    if (isReconnecting) return;
    setIsReconnecting(true);
    try {
      await api.post('/dashboard/mqtt-reconnect');
      // Wait 2 seconds for MQTT to establish connection before refreshing status
      setTimeout(() => {
        fetchData();
        setIsReconnecting(false);
      }, 2000);
    } catch (err) {
      console.error("Failed to reconnect MQTT", err);
      setIsReconnecting(false);
    }
  };

  if (loading) return <div className="animate-pulse flex space-x-4 p-6">Memuat dashboard...</div>;
  if (!metrics || !deviceStatus) return <div className="p-6">Gagal memuat data.</div>;

  const isSafe = alerts.length === 0;
  const hasDanger = alerts.some(a => a.severity === 'danger');
  const safetyStatus = isSafe ? 'Aman' : (hasDanger ? 'Bahaya' : 'Peringatan');
  const safetyColor = isSafe ? 'text-green-600 bg-green-50 border-green-200' : (hasDanger ? 'text-red-600 bg-red-50 border-red-200' : 'text-orange-600 bg-orange-50 border-orange-200');
  const SafetyIcon = isSafe ? CheckCircle : AlertTriangle;

  const topCards = [
    { label: 'Suhu Kandang', value: `${metrics.sensor.temperature}°C`, icon: ThermometerSun, color: 'text-orange-500', bg: 'bg-orange-50', border: 'border-orange-100' },
    { label: 'Kelembapan', value: `${metrics.sensor.humidity}%`, icon: Droplets, color: 'text-blue-500', bg: 'bg-blue-50', border: 'border-blue-100' },
    { label: 'Berat Maggot', value: `${metrics.produksi.berat_maggot} kg`, icon: Scale, color: 'text-emerald-500', bg: 'bg-emerald-50', border: 'border-emerald-100' },
    { label: 'Total Produksi', value: `Rp ${(metrics.produksi.total_produksi * 7000).toLocaleString('id-ID')}`, icon: TrendingUp, color: 'text-indigo-500', bg: 'bg-indigo-50', border: 'border-indigo-100' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Dashboard Overview</h1>
          <p className="text-slate-500 mt-1">Status kandang BSF real-time.</p>
        </div>
        
        <div className="flex items-center gap-3">
          {!deviceStatus.mqtt_connected && (
            <button 
              onClick={handleReconnect} 
              disabled={isReconnecting}
              className={`text-xs font-medium px-3 py-2 rounded-xl border transition-colors flex items-center gap-2 ${
                isReconnecting 
                  ? 'bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed' 
                  : 'bg-indigo-50 text-indigo-600 border-indigo-100 hover:bg-indigo-100 cursor-pointer'
              }`}
            >
              <span className={isReconnecting ? 'animate-spin' : ''}>🔄</span>
              {isReconnecting ? 'Menyambungkan...' : 'Sambung Ulang MQTT'}
            </button>
          )}
          
          <div className={`px-4 py-2 rounded-xl border flex items-center gap-2 font-bold ${safetyColor}`}>
            <SafetyIcon size={18} />
            Status: {safetyStatus}
          </div>
          
          <div className={`px-3 py-2 rounded-xl border flex items-center gap-2 text-sm font-medium ${deviceStatus.mqtt_connected ? 'bg-teal-50 text-teal-700 border-teal-200' : 'bg-slate-100 text-slate-500 border-slate-200'}`}>
            {deviceStatus.mqtt_connected ? <Wifi size={16} /> : <WifiOff size={16} />}
            {deviceStatus.mqtt_connected ? 'MQTT Terhubung' : 'Terputus'}
          </div>
        </div>
      </div>

      {/* Top Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {topCards.map((m, i) => {
          const Icon = m.icon;
          return (
            <div key={i} className={`bg-white rounded-xl p-5 border shadow-sm ${m.border}`}>
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm font-semibold text-slate-500 mb-1">{m.label}</p>
                  <h3 className="text-2xl font-bold text-slate-800">{m.value}</h3>
                </div>
                <div className={`p-2.5 rounded-lg ${m.bg} ${m.color}`}>
                  <Icon size={20} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Sparklines & Settings */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm flex flex-col">
            <h3 className="font-bold text-slate-800 mb-4 flex items-center justify-between">
              Tren Suhu & Kelembapan
              <span className="text-xs font-normal text-slate-400 bg-slate-100 px-2 py-1 rounded">100 data terakhir</span>
            </h3>
            <div className="h-48 w-full mt-2">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 0, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="timestamp" hide />
                  <YAxis domain={['dataMin - 2', 'dataMax + 2']} hide />
                  <Tooltip 
                    contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    labelStyle={{ color: '#64748b', marginBottom: '8px', fontWeight: 'bold' }}
                  />
                  <Line type="monotone" dataKey="temperature" name="Suhu (°C)" stroke="#f97316" strokeWidth={3} dot={false} activeDot={{ r: 6, strokeWidth: 0 }} />
                  <Line type="monotone" dataKey="humidity" name="Kelembapan (%)" stroke="#3b82f6" strokeWidth={3} dot={false} activeDot={{ r: 6, strokeWidth: 0 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-6 mt-4 text-sm font-medium">
              <span className="flex items-center gap-2 text-orange-600"><span className="w-3 h-3 rounded-full bg-orange-500"></span> Suhu (°C)</span>
              <span className="flex items-center gap-2 text-blue-600"><span className="w-3 h-3 rounded-full bg-blue-500"></span> Kelembapan (%)</span>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 border border-slate-200 shadow-sm grid grid-cols-2 gap-4">
            <div>
              <div className="flex items-center justify-between pr-4">
                <p className="text-slate-500 font-medium text-sm">Fase Saat Ini</p>
                {!isEditingPhase && (
                  <button onClick={() => { setIsEditingPhase(true); setSelectedPhase(deviceStatus.active_phase); }} className="text-xs text-blue-600 font-medium hover:underline">Ubah</button>
                )}
              </div>
              
              {isEditingPhase ? (
                <div className="mt-2 flex flex-col gap-2">
                  <select 
                    value={selectedPhase} 
                    onChange={e => setSelectedPhase(e.target.value)}
                    className="text-sm p-1.5 border rounded-lg outline-none"
                  >
                    <option value="Auto">Otomatis (Berdasarkan Umur)</option>
                    <option value="Telur">Telur</option>
                    <option value="Larva">Larva</option>
                    <option value="Prepupa">Prepupa</option>
                    <option value="Pupa">Pupa</option>
                    <option value="Lalat Dewasa">Lalat Dewasa</option>
                  </select>
                  <div className="flex gap-2">
                    <button onClick={handleUpdatePhase} disabled={isUpdatingPhase} className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded-md hover:bg-blue-700 disabled:opacity-50">
                      Simpan
                    </button>
                    <button onClick={() => setIsEditingPhase(false)} className="text-xs bg-slate-100 text-slate-600 px-3 py-1.5 rounded-md hover:bg-slate-200">
                      Batal
                    </button>
                  </div>
                </div>
              ) : (
                <p className="font-bold text-slate-800 text-lg mt-1 flex items-center gap-2">
                  {deviceStatus.active_phase}
                  {deviceStatus.is_auto ? 
                    <span className="text-xs font-normal bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full border border-indigo-100">Auto</span> : 
                    <span className="text-xs font-normal bg-amber-50 text-amber-600 px-2 py-0.5 rounded-full border border-amber-100">Manual</span>
                  }
                </p>
              )}
            </div>
            <div>
              <p className="text-slate-500 font-medium text-sm">Update Terakhir</p>
              <p className="font-semibold text-slate-700 mt-1">
                {deviceStatus.last_seen 
                  ? new Date(deviceStatus.last_seen.replace(" ", "T") + "Z").toLocaleString('id-ID') 
                  : "Belum ada data"}
              </p>
            </div>
            <div className="col-span-2 pt-4 border-t mt-2">
              <p className="text-slate-500 font-medium text-sm mb-2">Ambang Batas Aktif</p>
              <div className="flex gap-6">
                <div className="text-orange-600 font-medium bg-orange-50 px-3 py-1.5 rounded-lg border border-orange-100">
                  🌡️ {deviceStatus.active_threshold.tempMin}°C - {deviceStatus.active_threshold.tempMax}°C
                </div>
                <div className="text-blue-600 font-medium bg-blue-50 px-3 py-1.5 rounded-lg border border-blue-100">
                  💧 {deviceStatus.active_threshold.humidMin}% - {deviceStatus.active_threshold.humidMax}%
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Notifications */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm flex flex-col h-full overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
            <h3 className="font-bold text-slate-800 flex items-center gap-2">
              <Bell size={18} className="text-slate-500" />
              Notifikasi Unread
            </h3>
            {alerts.length > 0 && (
              <button onClick={markAlertsRead} className="text-xs font-medium text-blue-600 hover:text-blue-800 bg-blue-50 px-2 py-1 rounded">
                Tandai Dibaca
              </button>
            )}
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-3 max-h-[400px]">
            {alerts.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 py-10">
                <CheckCircle size={32} className="mb-2 opacity-50 text-green-500" />
                <p className="text-sm">Semua kondisi aman.</p>
              </div>
            ) : (
              alerts.map(a => (
                <div key={a.id} className={`p-3 rounded-lg border text-sm ${
                  a.severity === 'danger' ? 'bg-red-50 border-red-200 text-red-900' : 'bg-orange-50 border-orange-200 text-orange-900'
                }`}>
                  <div className="flex items-start gap-2">
                    <AlertTriangle size={16} className={`mt-0.5 flex-shrink-0 ${a.severity === 'danger' ? 'text-red-500' : 'text-orange-500'}`} />
                    <div>
                      <p className="font-bold">{a.severity.toUpperCase()}</p>
                      <p className="mt-0.5">{a.message}</p>
                      <p className="text-xs mt-2 opacity-70">{a.created_at}</p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
