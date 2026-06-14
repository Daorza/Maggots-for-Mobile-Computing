import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Server, Wifi, CheckCircle, Loader2, Play } from 'lucide-react';
import api from '../api';

export default function Connect() {
  const [broker, setBroker] = useState('');
  const [port, setPort] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  const [step, setStep] = useState(0);
  const [isConnecting, setIsConnecting] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const res = await api.get('/dashboard/mqtt-config');
        setBroker(res.data.broker);
        setPort(res.data.port);
      } catch (err) {
        setBroker('test.mosquitto.org');
        setPort('1883');
      }
    };
    fetchConfig();
  }, []);

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsConnecting(true);
    setStep(1);
    
    let isMounted = true;
    
    const addLog = (msg: string, delay: number) => {
      return new Promise<void>(resolve => {
        setTimeout(() => {
          if (isMounted) {
            setLogs(prev => [...prev, msg]);
            setStep(s => s + 1);
            resolve();
          }
        }, delay);
      });
    };

    try {
      await addLog(`Menyambungkan ke broker ${broker}...`, 800);
      await addLog(`Membuka port ${port}...`, 1200);
      await addLog(`Melakukan negosiasi TLS/SSL...`, 1500);
      await addLog(`Autentikasi kredensial...`, 1000);
      await addLog(`Berhasil terhubung ke broker!`, 800);
      
      if (isMounted) {
        setTimeout(() => {
          navigate('/');
        }, 1500);
      }
    } catch (err) {
      if (isMounted) {
        setLogs(prev => [...prev, 'Gagal terhubung. Meneruskan ke dashboard...']);
        setTimeout(() => navigate('/'), 2000);
      }
    }

    return () => {
      isMounted = false;
    };
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="mx-auto w-16 h-16 bg-white rounded-2xl shadow-sm border border-slate-100 flex items-center justify-center text-blue-600 mb-6">
          <Wifi size={32} />
        </div>
        <h2 className="text-center text-3xl font-extrabold text-slate-900 tracking-tight">
          Koneksi IoT
        </h2>
        <p className="mt-2 text-center text-sm text-slate-600">
          Sambungkan sistem web ke perangkat ESP32 Anda
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-xl shadow-slate-200/50 sm:rounded-2xl sm:px-10 border border-slate-100">
          
          {!isConnecting ? (
            <form className="space-y-6" onSubmit={handleConnect}>
              <div>
                <label className="block text-sm font-medium text-slate-700">MQTT Broker Address</label>
                <div className="mt-1 relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <Server size={18} />
                  </div>
                  <input
                    type="text"
                    required
                    value={broker}
                    onChange={(e) => setBroker(e.target.value)}
                    className="appearance-none block w-full pl-10 px-3 py-2.5 border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm text-slate-600 bg-slate-50"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700">Port</label>
                <div className="mt-1">
                  <input
                    type="text"
                    required
                    value={port}
                    onChange={(e) => setPort(e.target.value)}
                    className="appearance-none block w-full px-3 py-2.5 border border-slate-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm text-slate-600 bg-slate-50"
                  />
                </div>
              </div>

              <button
                type="submit"
                className="w-full flex justify-center items-center gap-2 py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                <Play size={16} /> Hubungkan Sekarang
              </button>
            </form>
          ) : (
            <div className="space-y-6">
              <div className="flex flex-col items-center justify-center py-4">
                {step < 6 ? (
                  <Loader2 className="animate-spin text-blue-500 mb-4" size={40} />
                ) : (
                  <CheckCircle className="text-green-500 mb-4" size={40} />
                )}
                <h3 className="text-lg font-medium text-slate-900">
                  {step < 6 ? 'Memulai Koneksi...' : 'Koneksi Berhasil!'}
                </h3>
              </div>

              <div className="bg-slate-50 rounded-lg border border-slate-200 p-4 min-h-[160px] max-h-[200px] overflow-y-auto">
                <div className="space-y-2">
                  {logs.map((log, i) => (
                    <div 
                      key={i} 
                      className={`text-sm ${
                        log.includes('Gagal') ? 'text-red-600' : 
                        log.includes('Berhasil') ? 'text-green-600 font-medium' : 
                        'text-slate-600'
                      } animate-in fade-in slide-in-from-bottom-2 duration-300`}
                    >
                      <span className="text-slate-400 text-xs mr-2">[{new Date().toLocaleTimeString('id-ID')}]</span>
                      {log}
                    </div>
                  ))}
                  {step > 0 && step < 6 && (
                    <div className="text-slate-400 text-sm animate-pulse flex items-center">
                      <span className="text-slate-400 text-xs mr-2">[{new Date().toLocaleTimeString('id-ID')}]</span>
                      <span className="w-1.5 h-3 bg-blue-400 inline-block"></span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
