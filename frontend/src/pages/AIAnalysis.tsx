import { useState, useRef, useEffect, useMemo } from 'react';
import { Bot, Send, User, MessageSquare, Plus, Trash2, History, X, Menu } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import api from '../api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface ChatSession {
  id: number;
  title: string;
  created_at: string;
}

const ALL_SUGGESTIONS = [
  "Apakah ada anomali suhu atau kelembapan yang tercatat hari ini?",
  "Berapa rata-rata suhu kandang dan dampaknya terhadap perkembangan maggot?",
  "Bagaimana tren pemberian pakan berdasarkan catatan terakhir?",
  "Berikan ringkasan kondisi operasional kandang beserta insight untuk meningkatkannya.",
  "Berdasarkan data hari ini, apakah ada tindakan korektif yang harus segera saya ambil?",
  "Apakah berat maggot saat ini sudah sesuai dengan target rata-rata fase ini?",
  "Tolong hitung total estimasi keuntungan jika saya memanen semua maggot sekarang.",
  "Bandingkan kondisi kandang minggu lalu dengan minggu ini.",
  "Apakah cuaca atau kelembapan memengaruhi nafsu makan maggot akhir-akhir ini?",
  "Sebutkan 3 hal yang bisa saya tingkatkan untuk panen siklus berikutnya."
];

export default function AIAnalysis() {
  const [chats, setChats] = useState<ChatSession[]>([]);
  const [activeChatId, setActiveChatId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Pick 4 random suggestions
  const currentSuggestions = useMemo(() => {
    const shuffled = [...ALL_SUGGESTIONS].sort(() => 0.5 - Math.random());
    return shuffled.slice(0, 4);
  }, [activeChatId]);

  const loadChats = async () => {
    try {
      const res = await api.get('/ai/chats');
      setChats(res.data);
    } catch (err) {
      console.error("Gagal memuat daftar chat:", err);
    }
  };

  const loadChatMessages = async (chatId: number) => {
    try {
      const res = await api.get(`/ai/chats/${chatId}`);
      setMessages(res.data);
      setActiveChatId(chatId);
      setError('');
      setIsSidebarOpen(false); // Close sidebar on mobile/desktop after picking
    } catch (err) {
      console.error("Gagal memuat pesan chat:", err);
      setError("Gagal memuat obrolan.");
    }
  };

  const deleteChat = async (e: React.MouseEvent, chatId: number) => {
    e.stopPropagation();
    if (!window.confirm("Hapus percakapan ini?")) return;
    try {
      await api.delete(`/ai/chats/${chatId}`);
      if (activeChatId === chatId) {
        startNewChat();
      }
      loadChats();
    } catch (err) {
      console.error("Gagal menghapus chat:", err);
    }
  };

  const startNewChat = () => {
    setActiveChatId(null);
    setMessages([]);
    setPrompt('');
    setError('');
    setIsSidebarOpen(false);
  };

  useEffect(() => {
    loadChats();
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleAnalyze = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!prompt.trim()) return;

    const currentPrompt = prompt;
    setPrompt('');
    setError('');

    const newMessages: Message[] = [...messages, { role: 'user', content: currentPrompt }];
    setMessages(newMessages);
    setLoading(true);

    try {
      const payload: any = {
        prompt: currentPrompt,
        history: messages
      };
      if (activeChatId) {
        payload.chat_id = activeChatId;
      }

      const res = await api.post('/ai/analyze', payload);
      setMessages([...newMessages, { role: 'assistant', content: res.data.analysis }]);

      if (!activeChatId && res.data.chat_id) {
        setActiveChatId(res.data.chat_id);
        loadChats();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Terjadi kesalahan saat memproses AI.');
      setPrompt(currentPrompt);
      setMessages(messages);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative h-[calc(100vh-8rem)] w-full overflow-hidden">

      {/* Main Chat Area */}
      <div className={`transition-all duration-300 h-full flex flex-col bg-white p-4 md:p-6 rounded-xl border border-slate-200 shadow-sm ${isSidebarOpen ? 'md:ml-80' : ''}`}>
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="p-3 bg-purple-50 hover:bg-purple-100 text-purple-600 rounded-xl transition-colors flex items-center justify-center"
              title="Riwayat Chat"
            >
              <Menu size={24} />
            </button>
            <div>
              <h1 className="text-xl md:text-2xl font-bold text-slate-800 tracking-tight">AI Analysis</h1>
            </div>
          </div>
          <div className="p-3 bg-purple-50 text-purple-600 rounded-xl hidden md:block">
            <Bot size={24} />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto mb-4 p-4 bg-slate-50 rounded-xl border border-slate-100 flex flex-col gap-4">
          {messages.length === 0 && !loading && !error && (
            <div className="h-full flex flex-col items-center justify-center text-slate-400">
              <Bot size={48} className="mb-4 opacity-50" />
              <p className="mb-6 text-slate-500 font-medium text-center">Tanyakan sesuatu tentang kondisi kandang Anda</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl px-4">
                {currentSuggestions.map((suggestion, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setPrompt(suggestion);
                    }}
                    className="text-left p-3 rounded-xl border border-purple-100 bg-purple-50/50 hover:bg-purple-100/50 text-purple-700 text-sm transition-colors"
                  >
                    "{suggestion}"
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`flex gap-3 max-w-[90%] md:max-w-[80%] ${msg.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}>
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${msg.role === 'user' ? 'bg-slate-200 text-slate-600' : 'bg-purple-100 text-purple-600'}`}>
                {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div className={`p-3 rounded-2xl ${msg.role === 'user' ? 'bg-purple-600 text-white rounded-tr-sm' : 'bg-white border border-slate-200 rounded-tl-sm shadow-sm'}`}>
                {msg.role === 'user' ? (
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                ) : (
                  <div className="prose prose-sm prose-slate max-w-none">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-3 max-w-[80%]">
              <div className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center bg-purple-100 text-purple-600">
                <Bot size={16} />
              </div>
              <div className="p-4 bg-white border border-slate-200 rounded-2xl rounded-tl-sm shadow-sm flex items-center gap-2">
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse"></div>
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse delay-75"></div>
                <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse delay-150"></div>
              </div>
            </div>
          )}
          {error && <div className="text-red-500 text-sm text-center p-2 bg-red-50 rounded-lg border border-red-100">{error}</div>}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleAnalyze} className="relative mt-auto">
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

      {/* Overlay for mobile when sidebar is open */}
      {isSidebarOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/20 z-40"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sliding Sidebar Drawer */}
      <div className={`fixed md:absolute top-0 left-0 h-full w-80 bg-white border-r border-slate-200 shadow-xl z-50 transform transition-transform duration-300 flex flex-col p-4 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-bold text-slate-800">Riwayat Obrolan</h2>
          <button
            onClick={() => setIsSidebarOpen(false)}
            className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <button
          onClick={startNewChat}
          className="flex items-center gap-2 justify-center w-full p-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium text-sm shadow-sm mb-4 flex-shrink-0"
        >
          <Plus size={18} />
          <span>Percakapan Baru</span>
        </button>

        <div className="flex-1 overflow-y-auto pr-1 space-y-1">
          {chats.length === 0 ? (
            <p className="text-xs text-slate-400 text-center py-4">Belum ada percakapan</p>
          ) : (
            chats.map((chat) => (
              <div
                key={chat.id}
                onClick={() => loadChatMessages(chat.id)}
                className={`group flex items-center justify-between p-3 rounded-xl cursor-pointer transition-colors ${activeChatId === chat.id ? 'bg-purple-50 border border-purple-100' : 'hover:bg-slate-50 border border-transparent'}`}
              >
                <div className="flex items-center gap-3 overflow-hidden">
                  <MessageSquare size={16} className={`flex-shrink-0 ${activeChatId === chat.id ? 'text-purple-600' : 'text-slate-400'}`} />
                  <span className={`text-sm truncate ${activeChatId === chat.id ? 'font-medium text-purple-700' : 'text-slate-600'}`}>
                    {chat.title}
                  </span>
                </div>
                <button
                  onClick={(e) => deleteChat(e, chat.id)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-red-500 rounded transition-opacity flex-shrink-0"
                  title="Hapus obrolan"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
