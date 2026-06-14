import { BookOpen } from 'lucide-react';

const CARDS = [
  {
    icon: "🪲",
    title: "Apa itu Maggot BSF?",
    shortDesc: "Larva Black Soldier Fly pengurai limbah organik berkecepatan tinggi.",
    longBody: "Larva Black Soldier Fly (Hermetia illucens) mampu mengurai limbah organik dengan cepat dan menghasilkan biomassa bernilai tinggi sebagai pakan ternak, pupuk organik (frass), dan sumber protein."
  },
  {
    icon: "♻️",
    title: "Circular Economy",
    shortDesc: "Ubah sampah organik menjadi protein, frass, dan nilai ekonomi.",
    longBody: "Budidaya BSF mengubah sampah organik menjadi protein hewani, frass sebagai pupuk organik, dan nilai ekonomi baru untuk pertanian lokal. Ini mewujudkan konsep ekonomi sirkular yang nyata."
  },
  {
    icon: "🌱",
    title: "Cara Budidaya",
    shortDesc: "Jaga kondisi kandang dan catat data secara berkala.",
    longBody: "Jaga suhu, kelembapan, kepadatan populasi, dan kualitas pakan. Catat pakan serta berat secara berkala untuk memantau performa koloni dan mengoptimalkan konversi limbah."
  },
  {
    icon: "🍽️",
    title: "Manajemen Pakan",
    shortDesc: "Berikan pakan bertahap, hindari bahan terlalu basah.",
    longBody: "Berikan pakan bertahap sesuai kapasitas koloni. Hindari bahan terlalu basah atau berminyak. Pantau sisa pakan secara rutin untuk mencegah bau dan kontaminasi."
  },
  {
    icon: "📊",
    title: "Panen dan Evaluasi",
    shortDesc: "Hitung efisiensi konversi dari data pakan dan produksi.",
    longBody: "Bandingkan total sampah masuk, berat maggot panen, dan kondisi lingkungan untuk menghitung Feed Conversion Ratio (FCR). Gunakan data ini untuk mengoptimalkan siklus produksi berikutnya."
  }
];

export default function Edukasi() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Pusat Edukasi</h1>
          <p className="text-slate-500 mt-1">Materi singkat budidaya BSF dan pengelolaan limbah organik.</p>
        </div>
        <div className="p-3 bg-teal-50 text-teal-600 rounded-xl">
          <BookOpen size={24} />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {CARDS.map((c, i) => (
          <div key={i} className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden hover:shadow-md transition-shadow group">
            <div className="p-6">
              <div className="text-4xl mb-4 bg-slate-50 w-16 h-16 rounded-2xl flex items-center justify-center border border-slate-100 group-hover:scale-110 transition-transform">
                {c.icon}
              </div>
              <h3 className="text-lg font-bold text-slate-800 mb-2">{c.title}</h3>
              <p className="text-sm font-medium text-slate-500 mb-4">{c.shortDesc}</p>
              
              <details className="group/details">
                <summary className="text-sm font-semibold text-teal-600 cursor-pointer hover:text-teal-700 list-none flex items-center outline-none">
                  Lihat selengkapnya
                  <span className="ml-2 transition-transform group-open/details:rotate-180">↓</span>
                </summary>
                <p className="mt-3 text-sm text-slate-600 leading-relaxed border-t border-slate-100 pt-3">
                  {c.longBody}
                </p>
              </details>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
