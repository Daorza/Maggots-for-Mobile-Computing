import { useState } from 'react';
import { Bot, Send } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import api from '../api';

export default function AIAnalysis() {
  const [prompt, setPrompt] = useState('Berdasarkan data saat ini, apakah ada anomali yang perlu saya perhatikan?');
  const [analysis, setAnalysis] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setAnalysis('');
    
    try {
      const res = await api.post('/ai/analyze', { prompt });
      setAnalysis(res.data.analysis);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Terjadi kesalahan saat memproses AI.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight">AI Analysis</h1>
          <p className="text-slate-500 mt-1">Dapatkan insight otomatis dari asisten cerdas Llama 3.3.</p>
        </div>
        <div className="p-3 bg-purple-50 text-purple-600 rounded-xl">
          <Bot size={24} />
        </div>
      </div>

      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col h-[500px]">
        <div className="flex-1 overflow-y-auto mb-4 p-4 bg-slate-50 rounded-xl border border-slate-100">
          {error && <div className="text-red-500 text-sm">{error}</div>}
          {!analysis && !loading && !error && (
            <div className="h-full flex flex-col items-center justify-center text-slate-400">
              <Bot size={48} className="mb-4 opacity-50" />
              <p>Tanyakan sesuatu tentang kondisi kandang Anda.</p>
            </div>
          )}
          {loading && (
            <div className="flex items-center gap-3 text-purple-600 font-medium">
              <div className="animate-pulse flex space-x-2">
                <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
                <div className="w-2 h-2 bg-purple-400 rounded-full animation-delay-200"></div>
                <div className="w-2 h-2 bg-purple-400 rounded-full animation-delay-400"></div>
              </div>
              Sedang menganalisis data...
            </div>
          )}
          {analysis && (
            <div className="prose prose-sm prose-slate max-w-none">
              <ReactMarkdown>{analysis}</ReactMarkdown>
            </div>
          )}
        </div>
        
        <form onSubmit={handleAnalyze} className="relative">
          <input
            type="text"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={loading}
            className="w-full pl-4 pr-12 py-3 bg-white border border-slate-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none shadow-sm disabled:bg-slate-50 disabled:text-slate-400"
            placeholder="Tanyakan analisis..."
          />
          <button 
            type="submit" 
            disabled={loading || !prompt.trim()}
            className="absolute right-2 top-2 p-1.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
