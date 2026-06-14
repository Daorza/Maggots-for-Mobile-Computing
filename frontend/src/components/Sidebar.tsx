import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Activity, Edit3, Bot, FileText, BookOpen, LogOut } from 'lucide-react';
import clsx from 'clsx';

const menuItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/monitoring', label: 'Monitoring', icon: Activity },
  { path: '/input', label: 'Input Data', icon: Edit3 },
  { path: '/ai', label: 'AI Analysis', icon: Bot },
  { path: '/laporan', label: 'Laporan', icon: FileText },
  { path: '/edukasi', label: 'Edukasi', icon: BookOpen },
];

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const userName = localStorage.getItem('userName') || 'User';

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userName');
    navigate('/login');
  };

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col shadow-sm">
      <div className="p-6 border-b border-slate-100 flex flex-col items-center">
        <div className="w-12 h-12 bg-green-50 rounded-xl flex items-center justify-center text-green-600 mb-3 shadow-sm">
          <Bot size={24} />
        </div>
        <h1 className="text-xl font-extrabold text-slate-800 tracking-tight">Smart Maggot</h1>
      </div>

      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4 px-3">
          Menu Utama
        </div>
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                isActive
                  ? 'bg-green-50 text-green-700 shadow-sm border border-green-100/50'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              )}
            >
              <Icon size={18} className={isActive ? 'text-green-600' : 'text-slate-400'} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-100">
        <div className="flex items-center gap-3 px-3 py-2 mb-2">
          <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-600 font-bold text-sm">
            {userName.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 overflow-hidden">
            <p className="text-sm font-medium text-slate-700 truncate">{userName}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-600 hover:bg-red-50 hover:text-red-600 transition-colors"
        >
          <LogOut size={18} />
          Logout
        </button>
      </div>
    </aside>
  );
}
