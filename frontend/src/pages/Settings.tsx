import { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Save, AlertTriangle } from 'lucide-react';
import api from '../api';

interface Threshold {
  phase: string;
  temperature_min: number;
  temperature_max: number;
  humidity_min: number;
  humidity_max: number;
}

export default function Settings() {
  const [thresholds, setThresholds] = useState<Threshold[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const fetchThresholds = async () => {
    try {
      const res = await api.get('/dashboard/thresholds');
      setThresholds(res.data.thresholds);
    } catch (err) {
      console.error(err);
      setErrorMsg('Gagal memuat data ambang batas.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchThresholds();
  }, []);

  const handleInputChange = (index: number, field: keyof Threshold, value: string) => {
    const newThresholds = [...thresholds];
    newThresholds[index] = {
      ...newThresholds[index],
      [field]: parseFloat(value) || 0
    };
    setThresholds(newThresholds);
  };

  const handleSave = async () => {
    setSaving(true);
    setSuccessMsg('');
    setErrorMsg('');
    try {
      await api.put('/dashboard/thresholds', { thresholds });
      setSuccessMsg('Ambang batas berhasil diperbarui!');
      setTimeout(() => setSuccessMsg(''), 3000);
    } catch (err) {
      console.error(err);
      setErrorMsg('Gagal menyimpan perubahan.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-6 animate-pulse">Memuat pengaturan...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Pengaturan Sistem</h1>
          <p className="text-slate-500 mt-1">
            Konfigurasi parameter operasional dan batas toleransi sensor.
          </p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-6 py-2.5 bg-green-600 text-white font-medium rounded-xl hover:bg-green-700 disabled:opacity-50 transition-colors shadow-sm"
        >
          <Save size={18} />
          {saving ? 'Menyimpan...' : 'Simpan Perubahan'}
        </button>
      </div>

      {successMsg && (
        <div className="bg-green-50 text-green-700 p-4 rounded-xl border border-green-200">
          {successMsg}
        </div>
      )}

      {errorMsg && (
        <div className="bg-red-50 text-red-700 p-4 rounded-xl border border-red-200">
          {errorMsg}
        </div>
      )}

      <div className="bg-white border border-slate-200 shadow-sm rounded-xl overflow-hidden">
        <div className="p-5 border-b border-slate-100 bg-slate-50 flex items-center gap-3">
          <AlertTriangle className="text-orange-500" size={20} />
          <div>
            <h2 className="font-bold text-slate-800">Ambang Batas Suhu & Kelembapan (Per Fase)</h2>
            <p className="text-xs text-slate-500">Nilai ini digunakan oleh sistem AI dan Peringatan untuk mendeteksi anomali.</p>
          </div>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-1 gap-6">
            {thresholds.map((th, index) => (
              <div key={th.phase} className="border border-slate-200 rounded-xl p-4 bg-slate-50/50 hover:border-blue-200 hover:shadow-sm transition-all">
                <h3 className="font-bold text-lg text-slate-700 mb-4 pb-2 border-b border-slate-200">
                  {th.phase}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

                  {/* Min Temp */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1">Suhu Min (°C)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={th.temperature_min}
                      onChange={(e) => handleInputChange(index, 'temperature_min', e.target.value)}
                      className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-slate-700"
                    />
                  </div>

                  {/* Max Temp */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1">Suhu Max (°C)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={th.temperature_max}
                      onChange={(e) => handleInputChange(index, 'temperature_max', e.target.value)}
                      className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-slate-700"
                    />
                  </div>

                  {/* Min Humid */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1">Kelembapan Min (%)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={th.humidity_min}
                      onChange={(e) => handleInputChange(index, 'humidity_min', e.target.value)}
                      className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-slate-700"
                    />
                  </div>

                  {/* Max Humid */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1">Kelembapan Max (%)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={th.humidity_max}
                      onChange={(e) => handleInputChange(index, 'humidity_max', e.target.value)}
                      className="w-full px-3 py-2 bg-white border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-slate-700"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
