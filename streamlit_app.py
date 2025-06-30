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
import qrcode
import base64
from collections import Counter

# ===================== KONFIGURASI APLIKASI =====================
st.set_page_config(page_title="Presensi Jemaat", page_icon="🙏")
st.title("📸 Scan QR Kehadiran Jemaat")

# ===================== KONEKSI GOOGLE SHEETS =====================
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)
client = gspread.authorize(creds)

# Presensi → sheet1 ; Data Jemaat → worksheet "data_jemaat"
sheet_presensi = client.open_by_key("1LI5D_rWMkek5CHnEbZgHW4BV_FKcS9TUP0icVlKK1kQ").sheet1
sheet_jemaat = client.open_by_key("1LI5D_rWMkek5CHnEbZgHW4BV_FKcS9TUP0icVlKK1kQ").worksheet("data_jemaat")

# ===================== MODE ADMIN CEK STATISTIK =====================
query_params = st.experimental_get_query_params()
is_admin = query_params.get("admin", ["false"])[0] == "true"

if is_admin:
    st.subheader("🔐 Admin Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == st.secrets["admin_user"] and password == st.secrets["admin_pass"]:
            st.success("✅ Login berhasil.")

            st.subheader("📊 Statistik Presensi")
            df_presensi = sheet_presensi.get_all_records()
            st.metric("Total Jemaat Hadir", len(df_presensi))

            tanggal_list = [r["Waktu"][:10] for r in df_presensi]
            st.bar_chart(Counter(tanggal_list))

            st.subheader("🆕 Tambah Jemaat Baru + QR Code")
            with st.form("form_jemaat"):
                new_id = st.text_input("ID Jemaat Baru")
                new_nama = st.text_input("Nama Jemaat Baru")
                submitted = st.form_submit_button("Generate QR & Tambah")

            if submitted and new_id and new_nama:
                sheet_jemaat.append_row([new_id, new_nama, ""])
                qr = qrcode.make(new_id)
                buffer = BytesIO()
                qr.save(buffer, format="PNG")
                img_data = buffer.getvalue()
                st.image(img_data, caption=f"QR Code untuk {new_nama}")
                b64 = base64.b64encode(img_data).decode()
                href = f'<a href="data:image/png;base64,{b64}" download="qr_{new_id}.png">📥 Download QR Code</a>'
                st.markdown(href, unsafe_allow_html=True)
            st.stop()
        else:
            st.error("❌ Username atau password salah.")

# ===================== SCAN QR DENGAN KAMERA =====================
img = st.camera_input("Silakan scan QR Code dari kartu jemaat Anda")

if img:
    st.image(img, caption="✅ Gambar berhasil ditangkap.")
    image = Image.open(img)
    decoded = decode(image)

    if decoded:
        qr_data = decoded[0].data.decode("utf-8")
        st.success(f"✅ QR Terdeteksi: {qr_data}")

        daftar_jemaat = sheet_jemaat.get_all_records()
        data_jemaat = next((j for j in daftar_jemaat if str(j["ID"]).strip() == qr_data), None)

        if not data_jemaat:
            st.error("🚫 ID Jemaat tidak ditemukan dalam database.")
            st.stop()

        nama_jemaat = data_jemaat["Nama"]
        foto_id = data_jemaat.get("File_ID_Foto", "").strip()

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
            sheet_presensi.append_row([waktu_str, qr_data, nama_jemaat])
            st.success(f"📝 Kehadiran {nama_jemaat} berhasil dicatat!")

            if foto_id:
                foto_url = f"https://drive.google.com/thumbnail?id={foto_id}"
                try:
                    st.image(foto_url, width=200, caption=f"🧍 Foto Jemaat: {nama_jemaat}")
                except:
                    st.warning("⚠️ Gagal memuat foto jemaat. Cek ID atau jenis file.")

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

        # === Jumlah total jemaat hadir hari ini ===
        jumlah_hadir_hari_ini = sum(
            1 for r in riwayat if tanggal_hari_ini in r["Waktu"]
        )
        st.info(f"📊 Total Jemaat Hadir Hari Ini: {jumlah_hadir_hari_ini}")

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
