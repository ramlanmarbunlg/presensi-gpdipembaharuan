# 📊 Sistem Presensi Online GPdI Pembaharuan

Sistem presensi jemaat berbasis **Streamlit** dan **Google Sheets** untuk memudahkan pencatatan kehadiran jemaat secara real-time dan otomatis. Fitur lengkap mencakup presensi QR code, deteksi ibadah berdasarkan jadwal, statistik mingguan–tahunan, dan dashboard ibadah.

---

## 🚀 Fitur Saat Ini (Stable)

### 🧾 Presensi Jemaat
- Presensi berbasis **QR Code** (berisi NIJ unik jemaat)
- Validasi jam presensi berdasarkan **jadwal ibadah** dari sheet `Ibadah`
- Otomatis mendeteksi apakah jemaat **"Tepat Waktu"** atau **"Terlambat"**
- Mencegah presensi ganda dalam 1 hari
- Presensi ditampilkan dalam daftar antrian live jemaat hadir

### 📋 Formulir Tambah Jemaat
- Input: ID, NIK, Nama, Tanggal Lahir, Jenis Kelamin, WA, Email
- Validasi:
  - NIK wajib 16 digit
  - Format nomor WA harus `628xxxxxxxx`
  - Email harus valid & tidak boleh duplikat
  - Cek duplikat No WA, Email, dan NIK
- Usia otomatis dihitung: `XX Tahun, XX Bulan, XX Hari`

### 📖 Master Data Ibadah (Sheet: `Ibadah`)
- Kolom: `No`, `Kode`, `Nama Ibadah`, `Lokasi`, `Hari`, `Jam`, `Keterangan`
- Fitur:
  - Tambah ibadah baru (kode otomatis `IBD-001`, `IBD-002`, ...)
  - Validasi duplikat nama ibadah
  - Tampilkan daftar ibadah secara otomatis
  - Edit/update data ibadah
  - Hapus ibadah (by name)

### 📊 Statistik Presensi Jemaat
- Total kehadiran jemaat
- Grafik kehadiran:
  - 📅 Mingguan (line chart)
  - 🗓️ Bulanan (bar chart)
  - 📆 Tahunan (line chart)
- Filter presensi berdasarkan:
  - Tahun → Bulan → Tanggal
  - Jenis Ibadah / Lokasi
- Jumlah kehadiran per jenis ibadah

### ⚠️ Optimalisasi & Penanganan Error
- Penggunaan `@st.cache_data` untuk menghindari API rate limit Google Sheets
- Penanganan:
  - `KeyError` untuk kolom tidak ditemukan
  - `AttributeError` untuk worksheet
  - `APIError: Quota exceeded` → dikurangi dengan caching
  - Validasi nama data (`if df.empty`)

---

## 🔧 Fitur Pengembangan Selanjutnya (📍Roadmap)

### 🎯 Jemaat & Admin
- [ ] Dashboard jemaat pribadi (lihat profil dan riwayat presensi)
- [ ] Login multi-role: admin, operator, jemaat, gembala
- [ ] Akun & password jemaat

### 🔁 Presensi Lanjutan
- [ ] Presensi berbasis selfie (upload realtime)
- [ ] Presensi dengan deteksi lokasi (GPS atau IP lokal)
- [ ] Sistem pengingat WA/email sebelum ibadah

### 📊 Statistik & Pelaporan
- [ ] Ekspor laporan ke PDF / Google Docs
- [ ] Riwayat tidak hadir selama 3 minggu berturut-turut
- [ ] Statistik kehadiran per jemaat bulanan

---

## ⚙️ Teknologi yang Digunakan

| Komponen         | Teknologi                   |
|------------------|-----------------------------|
| Frontend         | Python + [Streamlit](https://streamlit.io) |
| Backend Database | Google Sheets via `gspread` |
| QR Code          | `qrcode` Python package     |
| Caching          | `@st.cache_data`            |
| Grafik           | Streamlit `line_chart`, `bar_chart` |
| Timezone         | `zoneinfo` (Asia/Jakarta)   |

---

## 📁 Struktur Spreadsheet Google (Sheets yang digunakan)

### 📄 Sheet: `Jemaat`
- ID, NIK, NIJ, Nama, Jenis Kelamin, Tanggal Lahir, Usia, Foto, WA, Email, QR Code

### 📄 Sheet: `Presensi`
- Waktu, NIJ, Nama, Keterangan, Ibadah

### 📄 Sheet: `Ibadah`
- No, Kode, Nama Ibadah, Lokasi, Hari, Jam, Keterangan

---

## 💡 Lisensi & Kredit

Dikembangkan oleh tim GPdI Pembaharuan bersama OpenAI ChatGPT.  
Silakan fork dan gunakan untuk pelayanan Anda. Mohon tetap mencantumkan kredit pada versi publik.

---

## 🛠️ Cara Deploy
1. Clone repo ini
2. Atur Google Sheets dan aktifkan API
3. Jalankan dengan:
```bash
streamlit run streamlit_app.py

**## 📬 Kontak**
Jika ingin mengembangkan bersama atau butuh bantuan:
📧 Email: [ramlanmediakreatif@gmail.com]
📞 WA: 628xxxxxxxxxx
