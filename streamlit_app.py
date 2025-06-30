# ============================================
# PRESENSI JEMAAT STREAMLIT QR CAMERA (FINAL+)
# ============================================

import streamlit as st
from PIL import Image
from pyzbar.pyzbar import decode
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from zoneinfo import ZoneInfo
from reportlab.pdfgen import canvas
from io import BytesIO

# ===================== KONFIGURASI APLIKASI =====================
st.set_page_config(page_title="Presensi Jemaat", page_icon="🙏")
st.title("📸 Scan QR Kehadiran Jemaat")

# ===================== SCAN QR DENGAN KAMERA =====================
img = st.camera_input("Silakan scan QR Code dari kartu jemaat Anda")

if img:
    st.image(img, caption="✅ Gambar berhasil ditangkap.")
    image = Image.open(img)
    decoded = decode(image)

    if decoded:
        # Ambil data QR (biasanya ID Jemaat)
        qr_data = decoded[0].data.decode("utf-8")
        st.success(f"✅ QR Terdeteksi: {qr_data}")

        # ===================== KONEKSI KE GOOGLE SHEETS =====================
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.secrets["gcp_service_account"], scope
        )
        client = gspread.authorize(creds)

        # Presensi → sheet1 ; Data Jemaat → worksheet "data_jemaat"
        sheet_presensi = client.open_by_key("1LI5D_rWMkek5CHnEbZgHW4BV_FKcS9TUP0icVlKK1kQ").sheet1
        sheet_jemaat = client.open_by_key("1LI5D_rWMkek5CHnEbZgHW4BV_FKcS9TUP0icVlKK1kQ").worksheet("data_jemaat")

        # ===================== CARI DATA JEMAAT BERDASARKAN QR =====================
        daftar_jemaat = sheet_jemaat.get_all_records()
        data_jemaat = next((j for j in daftar_jemaat if str(j["ID"]).strip() == qr_data), None)

        if not data_jemaat:
            st.error("🚫 ID Jemaat tidak ditemukan dalam database.")
            st.stop()

        nama_jemaat = data_jemaat["Nama"]
        foto_id = data_jemaat.get("File_ID_Foto", "").strip()

        # ===================== BATASI PRESENSI 1x / HARI =====================
        waktu_wib = datetime.now(ZoneInfo("Asia/Jakarta"))
        tanggal_hari_ini = waktu_wib.strftime("%Y-%m-%d")
        waktu_str = waktu_wib.strftime("%Y-%m-%d %H:%M:%S")

        riwayat = sheet_presensi.get_all_records()
        sudah_presensi = any(
            r["ID"] == qr_data and tanggal_hari_ini in r["Waktu"]
            for r in riwayat
        )

        if sudah_presensi:
            waktu_terakhir = next(
                r["Waktu"] for r in riwayat if r["ID"] == qr_data and tanggal_hari_ini in r["Waktu"]
            )
            st.warning(f"⚠️ Anda sudah melakukan presensi hari ini pada {waktu_terakhir}")
        else:
            # ===================== SIMPAN PRESENSI =====================
            sheet_presensi.append_row([waktu_str, qr_data, nama_jemaat])
            st.success(f"📝 Kehadiran {nama_jemaat} berhasil dicatat!")

            # ===================== TAMPILKAN FOTO JIKA ADA =====================
            if foto_id:
                foto_url = f"https://drive.google.com/uc?id={foto_id}"
                st.image(foto_url, width=200, caption=f"🧍 Foto Jemaat: {nama_jemaat}")

            # ===================== CETAK SERTIFIKAT KEHADIRAN =====================
            buffer = BytesIO()
            c = canvas.Canvas(buffer)
            c.setFont("Helvetica-Bold", 18)
            c.drawString(100, 750, "SERTIFIKAT KEHADIRAN JEMAAT")
            c.setFont("Helvetica", 12)
            c.drawString(100, 700, f"Nama Jemaat : {nama_jemaat}")
            c.drawString(100, 680, f"ID Jemaat   : {qr_data}")
            c.drawString(100, 660, f"Waktu Hadir : {waktu_str}")
            c.drawString(100, 640, "Lokasi      : GPdI Pembaharuan Medan")
            c.save()
            buffer.seek(0)

            st.download_button(
                label="📥 Download Sertifikat Kehadiran",
                data=buffer,
                file_name=f"sertifikat_{qr_data}.pdf",
                mime="application/pdf"
            )

        # ===================== RIWAYAT PRESENSI JEMAAT =====================
        st.subheader("📋 Riwayat Presensi Jemaat Ini")
        riwayat_jemaat = [
            r for r in riwayat if r["ID"] == qr_data
        ]
        if riwayat_jemaat:
            st.table(riwayat_jemaat)
        else:
            st.info("Belum ada riwayat presensi sebelumnya.")

    else:
        st.error("❌ QR Code tidak terbaca. Silakan ulangi scan.")
