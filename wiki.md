
# 📚 Wiki: Sistem Presensi Online GPdI Pembaharuan

Selamat datang di Wiki proyek Presensi Online Jemaat. Halaman ini memberikan informasi tambahan mengenai cara kerja, modul, dan arsitektur sistem.

---

## 📌 Modul Utama

### 1. Presensi Jemaat
- Menggunakan QR Code sebagai identitas jemaat (NIJ)
- Otomatis mengenali ibadah berdasarkan hari dan jadwal ibadah
- Mencegah presensi ganda
- Keterangan otomatis: Tepat Waktu / Terlambat

### 2. Manajemen Data Jemaat
- Tambah, validasi, dan simpan data jemaat
- Hindari duplikat NIK, WA, Email
- Usia dihitung otomatis (Tahun, Bulan, Hari)

### 3. Master Data Ibadah
- Menyimpan daftar ibadah
- Mendukung tambah, edit, hapus ibadah
- Kode Ibadah otomatis (IBD-001, IBD-002, ...)

### 4. Statistik
- Analisis mingguan, bulanan, tahunan
- Filter berdasarkan ibadah/lokasi
- Ekspor CSV

---

## 🧱 Arsitektur

```
Streamlit App
│
├── Google Sheets:
│   ├── Jemaat
│   ├── Presensi
│   └── Ibadah
│
├── QR Generator API (qrserver)
└── Google Drive (Penyimpanan foto & QR)
```

---

## 🔐 Hak Akses

- Admin: Akses penuh seluruh tab
- Operator: Input presensi dan data jemaat
- Jemaat: Hanya melihat riwayat pribadi (fitur mendatang)

---
