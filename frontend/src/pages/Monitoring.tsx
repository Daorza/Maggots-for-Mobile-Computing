import { useEffect, useState, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Activity, RefreshCw } from 'lucide-react';
import api from '../api';

export default function Monitoring() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [limit, setLimit] = useState(100);

  const fetchData = async () => {
    try {
      const res = await api.get(`/dashboard/monitoring?limit=${limit}`);
      setData(res.data.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [limit]);

  const stats = useMemo(() => {
    if (data.length === 0) return null;
    const temps = data.map(d => d.temperature);
    const hums = data.map(d => d.humidity);
    return {
      temp: {
        min: Math.min(...temps).toFixed(1),
        max: Math.max(...temps).toFixed(1),
        avg: (temps.reduce((a, b) => a + b, 0) / temps.length).toFixed(1)
      },
      hum: {
        min: Math.min(...hums).toFixed(1),
        max: Math.max(...hums).toFixed(1),
        avg: (hums.reduce((a, b) => a + b, 0) / hums.length).toFixed(1)
      }
    };
  }, [data]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Monitoring Real-Time</h1>
          <p className="text-slate-500 mt-1">Grafik interaktif suhu dan kelembapan kandang BSF.</p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="bg-white p-1 rounded-lg border shadow-sm flex gap-2">
            <select 
              value={limit} 
              onChange={e => setLimit(Number(e.target.value))}
              className="px-3 py-1.5 text-sm font-medium text-slate-700 bg-transparent outline-none cursor-pointer"
            >
              <option value={50}>50 Titik Terakhir</option>
              <option value={100}>100 Titik Terakhir</option>
              <option value={300}>300 Titik Terakhir</option>
              <option value={500}>500 Titik Terakhir</option>
            </select>
          </div>
          <button 
            onClick={fetchData}
            className="p-2.5 bg-indigo-50 text-indigo-600 rounded-lg hover:bg-indigo-100 transition-colors border border-indigo-100"
            title="Refresh Data"
          >
            <RefreshCw size={18} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm md:col-span-3">
            <h3 className="text-sm font-bold text-slate-500 mb-3 flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-orange-500"></span> Analitik Suhu (°C)</h3>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div><p className="text-xs text-slate-400">Min</p><p className="text-lg font-semibold">{stats.temp.min}</p></div>
              <div><p className="text-xs text-slate-400">Avg</p><p className="text-lg font-bold text-orange-600">{stats.temp.avg}</p></div>
              <div><p className="text-xs text-slate-400">Max</p><p className="text-lg font-semibold">{stats.temp.max}</p></div>
            </div>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm md:col-span-3">
            <h3 className="text-sm font-bold text-slate-500 mb-3 flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-blue-500"></span> Analitik Kelembapan (%)</h3>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div><p className="text-xs text-slate-400">Min</p><p className="text-lg font-semibold">{stats.hum.min}</p></div>
              <div><p className="text-xs text-slate-400">Avg</p><p className="text-lg font-bold text-blue-600">{stats.hum.avg}</p></div>
              <div><p className="text-xs text-slate-400">Max</p><p className="text-lg font-semibold">{stats.hum.max}</p></div>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        {loading && data.length === 0 ? (
          <div className="h-[400px] flex items-center justify-center text-slate-400">Loading chart...</div>
        ) : data.length === 0 ? (
          <div className="h-[400px] flex items-center justify-center text-slate-400">Belum ada data sensor.</div>
        ) : (
          <div className="flex flex-col gap-6 w-full">
            <div className="h-[250px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data} margin={{ top: 10, right: 20, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(val) => val.split(' ')[1] || val} 
                    tick={{ fontSize: 12, fill: '#64748b' }}
                    tickLine={false}
                    axisLine={false}
                    minTickGap={30}
                    hide
                  />
                  <YAxis tick={{ fontSize: 12, fill: '#64748b' }} tickLine={false} axisLine={false} domain={['auto', 'auto']} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    labelStyle={{ color: '#64748b', marginBottom: '8px', fontWeight: 'bold' }}
                  />
                  <Legend iconType="circle" />
                  <Line type="monotone" dataKey="temperature" name="Suhu (°C)" stroke="#f97316" strokeWidth={2} dot={false} activeDot={{ r: 6, strokeWidth: 0 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            
            <div className="h-[250px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data} margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={(val) => val.split(' ')[1] || val} 
                    tick={{ fontSize: 12, fill: '#64748b' }}
                    tickLine={false}
                    axisLine={false}
                    minTickGap={30}
                  />
                  <YAxis tick={{ fontSize: 12, fill: '#64748b' }} tickLine={false} axisLine={false} domain={['auto', 'auto']} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                    labelStyle={{ color: '#64748b', marginBottom: '8px', fontWeight: 'bold' }}
                  />
                  <Legend iconType="circle" />
                  <Line type="monotone" dataKey="humidity" name="Kelembapan (%)" stroke="#3b82f6" strokeWidth={2} dot={false} activeDot={{ r: 6, strokeWidth: 0 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
