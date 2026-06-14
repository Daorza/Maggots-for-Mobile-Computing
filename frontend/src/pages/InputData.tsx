import { useState, useEffect } from 'react';
import { Edit3, CheckCircle2 } from 'lucide-react';
import api from '../api';

export default function InputData() {
  const [jenisPakan, setJenisPakan] = useState('');
  const [beratPakan, setBeratPakan] = useState('');
  const [tanggalPakan, setTanggalPakan] = useState(new Date().toISOString().split('T')[0]);
  const [catatanPangan, setCatatanPangan] = useState('');
  
  const [beratMaggot, setBeratMaggot] = useState('');
  const [tanggalMaggot, setTanggalMaggot] = useState(new Date().toISOString().split('T')[0]);
  const [catatanBerat, setCatatanBerat] = useState('');

  const [message, setMessage] = useState<{type: 'success'|'error', text: string} | null>(null);
  const [history, setHistory] = useState<{pangan: any[], berat: any[]}>({ pangan: [], berat: [] });

  const fetchHistory = async () => {
    try {
      const res = await api.get('/input/history');
      setHistory(res.data);
    } catch (err) {}
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const showMessage = (type: 'success'|'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const handlePangan = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/input/pangan', {
        jenis_pakan: jenisPakan,
        berat_pakan_kg: parseFloat(beratPakan),
        tanggal: tanggalPakan,
        notes: catatanPangan
      });
      showMessage('success', 'Data pangan berhasil disimpan!');
      setJenisPakan(''); setBeratPakan(''); setCatatanPangan('');
      fetchHistory();
    } catch (err: any) {
      showMessage('error', err.response?.data?.detail || 'Gagal menyimpan data.');
    }
  };

  const handleBerat = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/input/berat', {
        berat_maggot_kg: parseFloat(beratMaggot),
        tanggal: tanggalMaggot,
        notes: catatanBerat
      });
      showMessage('success', 'Data berat maggot berhasil disimpan!');
      setBeratMaggot(''); setCatatanBerat('');
      fetchHistory();
    } catch (err: any) {
      showMessage('error', err.response?.data?.detail || 'Gagal menyimpan data.');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Input Data</h1>
          <p className="text-slate-500 mt-1">Catat pakan organik dan berat maggot secara manual.</p>
        </div>
        <div className="p-3 bg-amber-50 text-amber-600 rounded-xl">
          <Edit3 size={24} />
        </div>
      </div>

      {message && (
        <div className={`p-4 rounded-lg flex items-center gap-3 ${message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
          {message.type === 'success' && <CheckCircle2 size={20} />}
          <p className="font-medium">{message.text}</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Form Pangan */}
        <div className="bg-white p-6 rounded-xl border-t-4 border-t-amber-400 border-x border-b border-slate-200 shadow-sm">
          <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">🌾 Input Pangan Organik</h3>
          <form onSubmit={handlePangan} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Jenis pakan</label>
              <input type="text" required value={jenisPakan} onChange={e => setJenisPakan(e.target.value)} placeholder="cth: sisa nasi, limbah sayur…" className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Berat pakan (kg)</label>
              <input type="number" step="0.1" required value={beratPakan} onChange={e => setBeratPakan(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Tanggal</label>
              <input type="date" required value={tanggalPakan} onChange={e => setTanggalPakan(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Catatan (opsional)</label>
              <textarea value={catatanPangan} onChange={e => setCatatanPangan(e.target.value)} rows={2} placeholder="Info tambahan..." className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none" />
            </div>
            <button type="submit" className="w-full py-2.5 bg-slate-900 text-white rounded-lg font-medium hover:bg-slate-800 transition-colors">
              💾 Simpan Pangan
            </button>
          </form>

          {history.pangan.length > 0 && (
            <div className="mt-8 bg-slate-50 p-4 rounded-lg border border-slate-100">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">5 Entri Terakhir</h4>
              <div className="space-y-2">
                {history.pangan.map((h, i) => (
                  <div key={i} className="flex flex-col text-sm border-b border-slate-100 pb-2">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">{h.date}</span>
                      <span className="font-medium text-slate-800">{h.feed_type}</span>
                      <span className="font-bold text-amber-600">{h.feed_weight_kg} kg</span>
                    </div>
                    {h.notes && <span className="text-xs text-slate-400 mt-1 italic">Catatan: {h.notes}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Form Berat */}
        <div className="bg-white p-6 rounded-xl border-t-4 border-t-emerald-400 border-x border-b border-slate-200 shadow-sm">
          <h3 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">⚖️ Input Berat Maggot</h3>
          <form onSubmit={handleBerat} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Berat Maggot (kg)</label>
              <input type="number" step="0.1" required value={beratMaggot} onChange={e => setBeratMaggot(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Tanggal</label>
              <input type="date" required value={tanggalMaggot} onChange={e => setTanggalMaggot(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Catatan (opsional)</label>
              <textarea value={catatanBerat} onChange={e => setCatatanBerat(e.target.value)} rows={2} placeholder="Info tambahan..." className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 outline-none" />
            </div>
            <button type="submit" className="w-full py-2.5 bg-slate-900 text-white rounded-lg font-medium hover:bg-slate-800 transition-colors mt-6">
              💾 Simpan Berat
            </button>
          </form>

          {history.berat.length > 0 && (
            <div className="mt-8 bg-slate-50 p-4 rounded-lg border border-slate-100">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">5 Entri Terakhir</h4>
              <div className="space-y-2">
                {history.berat.map((h, i) => (
                  <div key={i} className="flex flex-col text-sm border-b border-slate-100 pb-2">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">{h.date}</span>
                      <span className="font-bold text-emerald-600">{h.maggot_weight_kg} kg</span>
                    </div>
                    {h.notes && <span className="text-xs text-slate-400 mt-1 italic">Catatan: {h.notes}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
