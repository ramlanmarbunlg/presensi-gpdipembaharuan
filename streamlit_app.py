# ============================================
# PRESENSI JEMAAT STREAMLIT QR CAMERA (FINAL)
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

# ===================== KONFIGURASI =====================
st.set_page_config(page_title="Presensi Jemaat", page_icon="🙏")
st.title("📸 Scan QR Kehadiran Jemaat")

# ===================== KAMERA SCAN QR =====================
img = st.camera_input("Silakan scan QR Code dari kartu jemaat Anda")

if img:
    st.image(img, caption="Gambar QR Code berhasil ditangkap")
    image = Image.open(img)
    decoded = decode(image)

    if decoded:
        qr_data = decoded[0].data.decode("utf-8")
        st.success(f"✅ QR Terdeteksi: {qr_data}")

        # ===================== KONEKSI GOOGLE SHEET =====================
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.secrets["gcp_service_account"], scope
        )
        client = gspread.authorize(creds)

        # Presensi → Sheet1 | Database Jemaat → Sheet "data_jemaat"
        sheet_presensi = client.open_by_key("1LI5D_rWMkek5CHnEbZgHW4BV_FKcS9TUP0icVlKK1kQ").sheet1
        sheet_jemaat = client.open_by_key("1LI5D_rWMkek5CHnEbZgHW4BV_FKcS9TUP0icVlKK1kQ").worksheet("data_jemaat")

        # ===================== CARI NAMA DARI QR (ID Jemaat) =====================
        daftar_jemaat = sheet_jemaat.get_all_records()
        nama_jemaat = None
        for j in daftar_jemaat:
            if str(j["ID"]).strip() == qr_data:
                nama_jemaat = j["Nama"]
                break

        if not nama_jemaat:
            st.error("🚫 ID Jemaat tidak ditemukan di database.")
        else:
            # ===================== BATASI PRESENSI 1x/HARI =====================
            waktu_wib = datetime.now(ZoneInfo("Asia/Jakarta"))
            tanggal_hari_ini = waktu_wib.strftime("%Y-%m-%d")

            riwayat = sheet_presensi.get_all_records()
            sudah_presensi = False
            for r in riwayat:
                if r["ID"] == qr_data and tanggal_hari_ini in r["Waktu"]:
                    sudah_presensi = True
                    waktu_terakhir = r["Waktu"]
                    break

            if sudah_presensi:
                st.warning(f"⚠️ Anda sudah presensi hari ini pada {waktu_terakhir}")
            else:
                waktu_str = waktu_wib.strftime("%Y-%m-%d %H:%M:%S")
                sheet_presensi.append_row([waktu_str, qr_data, nama_jemaat])
                st.success(f"📝 Kehadiran {nama_jemaat} berhasil dicatat!")

                # ========== CETAK SERTIFIKAT ==========
                buffer = BytesIO()
                c = canvas.Canvas(buffer)
                c.setFont("Helvetica-Bold", 18)
                c.drawString(100, 750, "SERTIFIKAT KEHADIRAN JEMAAT")
                c.setFont("Helvetica", 12)
                c.drawString(100, 700, f"Nama Jemaat : {nama_jemaat}")
                c.drawString(100, 680, f"ID Jemaat   : {qr_data}")
                c.drawString(100, 660, f"Waktu Hadir : {waktu_str}")
                c.drawString(100, 640, "Lokasi      : Gereja ABC")
                c.save()
                buffer.seek(0)

                st.download_button(
                    label="📥 Download Sertifikat Kehadiran",
                    data=buffer,
                    file_name=f"sertifikat_{qr_data}.pdf",
                    mime="application/pdf"
                )

            # ===================== RIWAYAT PRESENSI =====================
            st.subheader("📋 Riwayat Presensi Sebelumnya")
            riwayat_jemaat = [
                r for r in riwayat if r["ID"] == qr_data
            ]
            if riwayat_jemaat:
                st.table(riwayat_jemaat)
            else:
                st.info("Belum ada riwayat presensi.")

    else:
        st.error("❌ QR Code tidak terdeteksi. Silakan coba lagi.")
