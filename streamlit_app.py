# ============================================
# PRESENSI JEMAAT STREAMLIT QR CAMERA (NEW)
# ============================================

import streamlit as st
from PIL import Image
from pyzbar.pyzbar import decode
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from reportlab.pdfgen import canvas
from io import BytesIO

# ===================== KONFIGURASI =====================
st.set_page_config(page_title="Presensi Jemaat", page_icon="🙏")
st.title("📸 Scan QR Kehadiran Jemaat")

# ===================== INPUT DARI KAMERA =====================
img = st.camera_input("Silakan scan QR Code dari kartu jemaat Anda")

if img:
    st.image(img, caption="Gambar QR Code berhasil ditangkap")
    image = Image.open(img)
    decoded = decode(image)

    if decoded:
        qr_data = decoded[0].data.decode("utf-8")
        st.success(f"✅ QR Terdeteksi: {qr_data}")

        # ===================== SIMPAN KE GOOGLE SHEETS =====================
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            st.secrets["gcp_service_account"], scope
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key("1LI5D_rWMkek5CHnEbZgHW4BV_FKcS9TUP0icVlKK1kQ").sheet1

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, qr_data])
        st.success("📝 Presensi berhasil dicatat.")

        # ===================== CETAK SERTIFIKAT =====================
        buffer = BytesIO()
        c = canvas.Canvas(buffer)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(100, 750, "SERTIFIKAT KEHADIRAN JEMAAT")
        c.setFont("Helvetica", 12)
        c.drawString(100, 700, f"Nama/ID Jemaat: {qr_data}")
        c.drawString(100, 680, f"Tanggal/Waktu: {now}")
        c.drawString(100, 660, "Lokasi: Gereja ABC")
        c.save()
        buffer.seek(0)

        st.download_button(
            label="🔖 Download Sertifikat Kehadiran",
            data=buffer,
            file_name="sertifikat_kehadiran.pdf",
            mime="application/pdf"
        )

    else:
        st.error("❌ Gagal membaca QR Code. Coba ulangi scan.")
