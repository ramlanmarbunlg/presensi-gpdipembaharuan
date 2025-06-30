# ============================================
# PRESENSI JEMAAT STREAMLIT QR CAMERA (FINAL++)
# ============================================

import streamlit as st
from PIL import Image
from pyzbar.pyzbar import decode
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time 
from zoneinfo import ZoneInfo
from reportlab.pdfgen import canvas
from io import BytesIO
from collections import Counter
import base64
import qrcode

# ===================== KONFIGURASI APLIKASI =====================
st.set_page_config(page_title="Presensi Jemaat", page_icon="🙏")

# ===================== SIDEBAR NAVIGASI =====================
halaman = st.sidebar.selectbox("📂 Pilih Halaman", ["📸 Presensi Jemaat", "🔐 Admin Panel"])

# ===================== KONEKSI GOOGLE SHEETS =====================
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
client = gspread.authorize(creds)

# Sheet utama
sheet_presensi = client.open_by_key("1LI5D_rWMkek5CHnEbZgHW4BV_FKcS9TUP0icVlKK1kQ").worksheet("presensi")
sheet_jemaat = client.open_by_key("1LI5D_rWMkek5CHnEbZgHW4BV_FKcS9TUP0icVlKK1kQ").worksheet("data_jemaat")

# ===================== HALAMAN PRESENSI =====================
if halaman == "📸 Presensi Jemaat":
    st.title("📸 Scan QR Kehadiran Jemaat")
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
                # Simpan presensi
                sheet_presensi.append_row([waktu_str, qr_data, nama_jemaat])
                st.success(f"📝 Kehadiran {nama_jemaat} berhasil dicatat!")

                # Tampilkan foto jemaat jika tersedia
                if foto_id:
                    foto_url = f"https://drive.google.com/thumbnail?id={foto_id}"
                    try:
                        st.image(foto_url, width=200, caption=f"🧍 Foto Jemaat: {nama_jemaat}")
                    except:
                        st.warning("⚠️ Gagal memuat foto jemaat. Cek ID atau jenis file.")

                # Unduh sertifikat
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
                st.download_button("📥 Download Sertifikat Kehadiran", buffer, f"sertifikat_{qr_data}.pdf", "application/pdf")

            # Tampilkan total kehadiran hari ini
            jumlah_hadir_hari_ini = sum(
                1 for r in riwayat if tanggal_hari_ini in r["Waktu"]
            )
            st.info(f"📊 Total Jemaat Hadir Hari Ini: {jumlah_hadir_hari_ini}")

            # Tampilkan riwayat presensi jemaat
            st.subheader("📋 Riwayat Presensi Jemaat Ini")
            riwayat_jemaat = [r for r in riwayat if r["ID"] == qr_data]
            if riwayat_jemaat:
                st.table(riwayat_jemaat)
            else:
                st.info("Belum ada riwayat presensi sebelumnya.")

        else:
            st.error("❌ QR Code tidak terbaca. Silakan ulangi scan.")

# ===================== HALAMAN ADMIN PANEL =====================
elif halaman == "🔐 Admin Panel":
    st.title("🔐 Admin: Kelola Data Jemaat")

    if "admin_login" not in st.session_state:
        st.session_state["admin_login"] = False

    if not st.session_state["admin_login"]:
        st.subheader("🔑 Login Admin")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username == st.secrets["login_admin"]["admin_user"] and password == st.secrets["login_admin"]["admin_pass"]:
                st.session_state["admin_login"] = True
                st.success("✅ Login berhasil")
                st.rerun()
            else:
                st.error("❌ Username atau password salah")

    else:
        st.success("👋 Selamat datang Admin!")

        # Statistik Presensi
        st.subheader("📊 Statistik Presensi")
        df_presensi = sheet_presensi.get_all_records()
        st.metric("🧍 Total Jemaat Hadir", len(df_presensi))
        tanggal_list = [r["Waktu"][:10] for r in df_presensi]
        st.bar_chart(Counter(tanggal_list))

        # =================== FORM TAMBAH JEMAAT BARU ===================
        st.subheader("🆕 Tambah Jemaat Baru")
        
        # Pilihan waktu delay sebelum reset otomatis (fleksibel)
        delay = st.slider("⏱️ Tampilkan pesan sukses selama (detik):", 1, 5, 2)
        
        # Ambil ID terakhir dari sheet
        daftar_id = [j["ID"] for j in sheet_jemaat.get_all_records()]
        angka_terakhir = max([int(i[1:]) for i in daftar_id if i.startswith("J")], default=0)
        id_baru = f"J{angka_terakhir + 1:03d}"
        
        # Gunakan form_key untuk bisa reset otomatis
        form_key = st.session_state.get("form_key", "form_jemaat_default")
        
        with st.form(key=form_key):
            st.text_input("ID Jemaat Baru", value=id_baru, disabled=True)
            nama_baru = st.text_input("Nama Jemaat Baru", key="input_nama")
        
            simpan = st.form_submit_button("💾 Simpan")
        
        # Simpan dan reset otomatis
        if simpan:
            if nama_baru.strip():
                sheet_jemaat.append_row([id_baru, nama_baru.strip(), ""])
                st.success(f"✅ Jemaat '{nama_baru}' berhasil ditambahkan dengan ID: {id_baru}")
                time.sleep(delay)  # waktu tampil pesan sukses sesuai slider
                st.session_state.form_key = f"form_{datetime.now().timestamp()}"
                st.experimental_rerun()
            else:
                st.warning("⚠️ Nama tidak boleh kosong.")
            
        # Upload Foto Jemaat
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseUpload
        from google.oauth2 import service_account
        
        st.subheader("🖼️ Upload Foto Jemaat ke Google Drive")
        
        # Waktu tampil pesan sukses
        delay_foto = st.slider("⏱️ Lama tampil pesan sukses (detik)", 1, 5, 3, key="slider_foto")
        
        # Ambil daftar jemaat
        daftar_jemaat = sheet_jemaat.get_all_records()
        opsi_jemaat = {f"{j['Nama']} ({j['ID']})": j['ID'] for j in daftar_jemaat}
        
        # Form input
        selected = st.selectbox("Pilih Jemaat", options=list(opsi_jemaat.keys()), key="select_jemaat")
        foto_file = st.file_uploader("Pilih File Foto (JPG/PNG)", type=["jpg", "jpeg", "png"], key="upload_foto")
        
        # ✅ Preview gambar sebelum upload
        if foto_file:
            st.image(foto_file, caption="📷 Preview Foto", use_column_width=True)
        
        # Tombol upload
        if st.button("📤 Upload Foto"):
            if selected and foto_file:
                credentials = service_account.Credentials.from_service_account_info(
                    st.secrets["gcp_service_account"]
                )
                drive_service = build("drive", "v3", credentials=credentials)
        
                # Upload file
                nama_file = f"foto_{opsi_jemaat[selected]}.jpg"
                media = MediaIoBaseUpload(foto_file, mimetype="image/jpeg")
                file_metadata = {
                    "name": nama_file,
                    "parents": [st.secrets["folder_id_drive_foto"]]
                }
                uploaded = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
                file_id = uploaded.get("id")
        
                # Update sheet
                baris_update = next(i + 2 for i, row in enumerate(daftar_jemaat) if row["ID"] == opsi_jemaat[selected])
                sheet_jemaat.update_cell(baris_update, 3, file_id)
        
                st.success(f"✅ Foto jemaat {selected} berhasil diupload ke Drive.")
                time.sleep(delay_foto)
        
                # Reset form
                st.session_state.select_jemaat = None
                st.session_state.upload_foto = None
                st.session_state.slider_foto = 3
                st.experimental_rerun()
            else:
                st.warning("⚠️ Lengkapi pilihan jemaat dan foto terlebih dahulu.")

        # Tombol logout
        if st.button("🔒 Logout Admin"):
            st.session_state["admin_login"] = False
            st.rerun()
