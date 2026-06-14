import { useEffect, useState } from 'react';
import { FileText, Download, Calendar } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../api';

export default function Laporan() {
  const [period, setPeriod] = useState('weekly');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchReport = async () => {
    setLoading(true);
    try {
      let url = `/reports/summary?period=${period}`;
      if (period === 'custom' && startDate && endDate) {
        url += `&start_date=${startDate}&end_date=${endDate}`;
      }
      const res = await api.get(url);
      setReport(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (period !== 'custom' || (startDate && endDate)) {
      fetchReport();
    }
  }, [period, startDate, endDate]);

  const metrics = report?.metrics || {};
  const chartData = report?.chart_data || [];

  const handleDownload = () => {
    if (!report) return;
    
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "Laporan Pertumbuhan Maggot\n\n";
    
    // Add Metrics
    csvContent += "Metrik,Nilai\n";
    csvContent += `Total Pakan,${metrics.total_feed || 0} kg\n`;
    csvContent += `Penambahan Berat,${metrics.weight_gain || 0} kg\n`;
    csvContent += `Suhu Rata-rata,${metrics.average_temperature || 0}°C\n`;
    csvContent += `Kelembapan Rata-rata,${metrics.average_humidity || 0}%\n`;
    csvContent += `Total Peringatan,${metrics.alert_count || 0}\n\n`;
    
    // Add Chart Data
    csvContent += "Tanggal,Berat (kg)\n";
    chartData.forEach((row: any) => {
      csvContent += `${row.date},${row.maggot_weight_kg}\n`;
    });
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `Laporan_Maggot_${period}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Laporan & Analitik</h1>
          <p className="text-slate-500 mt-1">Rekapitulasi pertumbuhan maggot dan sensor.</p>
        </div>
        
        <div className="flex gap-2 items-center bg-white p-1 rounded-lg border shadow-sm">
          <select 
            value={period} 
            onChange={(e) => setPeriod(e.target.value)}
            className="px-3 py-2 text-sm font-medium text-slate-700 bg-transparent outline-none cursor-pointer"
          >
            <option value="daily">Hari Ini</option>
            <option value="weekly">7 Hari Terakhir</option>
            <option value="monthly">30 Hari Terakhir</option>
            <option value="yearly">1 Tahun Terakhir</option>
            <option value="custom">Kustom...</option>
          </select>
          {period === 'custom' && (
            <div className="flex items-center gap-2 px-2 border-l">
              <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} className="text-sm outline-none" />
              <span className="text-slate-400">-</span>
              <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} className="text-sm outline-none" />
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border shadow-sm">
          <p className="text-sm text-slate-500 font-medium">Total Pakan</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">{loading ? '-' : `${metrics.total_feed} kg`}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border shadow-sm">
          <p className="text-sm text-slate-500 font-medium">Penambahan Berat</p>
          <p className="text-2xl font-bold text-emerald-600 mt-1">{loading ? '-' : `+${metrics.weight_gain} kg`}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border shadow-sm">
          <p className="text-sm text-slate-500 font-medium">Suhu Rata-rata</p>
          <p className="text-2xl font-bold text-orange-500 mt-1">{loading ? '-' : `${metrics.average_temperature}°C`}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border shadow-sm">
          <p className="text-sm text-slate-500 font-medium">Total Peringatan</p>
          <p className="text-2xl font-bold text-red-500 mt-1">{loading ? '-' : metrics.alert_count}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-bold text-slate-800">Tren Pertumbuhan Berat (kg)</h3>
            <button onClick={handleDownload} className="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors">
              <Download size={16} /> Unduh Laporan
            </button>
          </div>
          <div className="h-[300px]">
            {loading ? (
              <div className="h-full flex items-center justify-center text-slate-400">Loading chart...</div>
            ) : chartData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-400">Belum ada data di periode ini.</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 5, right: 0, bottom: 5, left: -20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#64748b' }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fontSize: 12, fill: '#64748b' }} tickLine={false} axisLine={false} />
                  <Tooltip cursor={{fill: '#f8fafc'}} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                  <Bar dataKey="maggot_weight_kg" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Berat (kg)" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col">
          <h3 className="font-bold text-slate-800 mb-4">Ringkasan Ekonomi</h3>
          <div className="flex-1 flex flex-col items-center justify-center bg-slate-50 rounded-xl border border-slate-100 p-6">
            <div className="text-sm font-medium text-slate-500 uppercase tracking-wide mb-2">Estimasi Nilai Produksi</div>
            <div className="text-3xl lg:text-4xl font-extrabold text-slate-800 tracking-tight text-center">
              {loading ? '-' : `Rp ${metrics.estimated_production_value?.toLocaleString('id-ID')}`}
            </div>
            <div className="text-sm text-slate-500 mt-4 bg-white px-3 py-1 rounded-full border border-slate-200 shadow-sm">
              Asumsi: Rp 7.000 / kg
            </div>
            <div className="mt-6 w-full text-sm text-slate-600 space-y-2">
              <div className="flex justify-between">
                <span>Berat Awal:</span>
                <span className="font-bold">{loading ? '-' : `${metrics.starting_weight} kg`}</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span>Berat Akhir:</span>
                <span className="font-bold">{loading ? '-' : `${metrics.latest_weight} kg`}</span>
              </div>
              <div className="flex justify-between pt-2">
                <span>Total Panen:</span>
                <span className="font-bold text-emerald-600">{loading ? '-' : `+${metrics.weight_gain} kg`}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
