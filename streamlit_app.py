# ============================================
# PRESENSI JEMAAT STREAMLIT QR CAMERA (V2)
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
import pandas as pd
def convert_to_csv(data):
    return pd.DataFrame(data).to_csv(index=False).encode('utf-8')
import re  # Tambahkan ini di atas file untuk validasi email/nomor
import smtplib
from email.message import EmailMessage
from email.mime.text import MIMEText
def kirim_email_selamat_datang(penerima_email, nama_jemaat):
    sender_email = st.secrets["email"]["from_email"]
    app_password = st.secrets["email"]["app_password"]

    subject = "Selamat Datang di Sistem Presensi GPdI Pembaharuan"
    body = f"""
    Shalom {nama_jemaat},

    Selamat datang di sistem kehadiran jemaat GPdI Pembaharuan Medan.
    Anda telah berhasil terdaftar dengan nama: {nama_jemaat}.

    Gunakan kartu atau QR Code Anda saat hadir di ibadah.

    Tuhan memberkati 🙏

    -- Admin GPdI Pembaharuan
    """

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = penerima_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"⚠️ Gagal mengirim email: {e}")
        return False

# ===================== KONFIGURASI APLIKASI =====================
st.set_page_config(page_title="Presensi Jemaat", page_icon="🙏")

# ===================== SIDEBAR NAVIGASI =====================
halaman = st.sidebar.selectbox("📂 Pilih Halaman", ["📸 Presensi Jemaat", "🔐 Admin Panel"])

# ===================== KONEKSI GOOGLE SHEETS =====================
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
client = gspread.authorize(creds)

sheet_presensi = client.open_by_key("1LI5D_rWMkek5CHnEbZgHW4BV_FKcS9TUP0icVlKK1kQ").worksheet("presensi")
sheet_jemaat = client.open_by_key("1LI5D_rWMkek5CHnEbZgHW4BV_FKcS9TUP0icVlKK1kQ").worksheet("data_jemaat")

# ===================== FUNGSI EMAIL =====================
def kirim_email(to_email, subject, body):
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = st.secrets["email"]["sender"]
        msg["To"] = to_email
        msg.set_content(body)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(st.secrets["email"]["sender"], st.secrets["email"]["password"])
        server.send_message(msg)
        server.quit()
    except Exception as e:
        st.warning(f"🚨 Gagal kirim email: {e}")

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
                st.error("🛑 ID Jemaat tidak ditemukan dalam database.")
                st.stop()

            nama_jemaat = data_jemaat["Nama"]
            email_jemaat = data_jemaat.get("Email", "")
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
                        st.image(foto_url, width=200, caption=f"🡭 Foto Jemaat: {nama_jemaat}")
                    except:
                        st.warning("⚠️ Gagal memuat foto jemaat.")

                # Kirim email ke jemaat
                if email_jemaat:
                    kirim_email(email_jemaat, "Kehadiran Jemaat GPdI", f"Syalom {nama_jemaat}, Presensi Anda pada {waktu_str} telah tercatat di sistem GPdI.")

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
                st.download_button("📅 Download Sertifikat Kehadiran", buffer, f"sertifikat_{qr_data}.pdf", "application/pdf")

            jumlah_hadir_hari_ini = sum(
                1 for r in riwayat if tanggal_hari_ini in r["Waktu"]
            )
            st.info(f"📊 Total Jemaat Hadir Hari Ini: {jumlah_hadir_hari_ini}")

            st.subheader("📋 Riwayat Presensi Jemaat Ini")
            riwayat_jemaat = [r for r in riwayat if r["ID"] == qr_data]
            st.table(riwayat_jemaat if riwayat_jemaat else "Belum ada riwayat.")

        else:
            st.error("❌ QR Code tidak terbaca. Silakan ulangi scan.")

# ===================== HALAMAN ADMIN PANEL =====================
elif halaman == "🔐 Admin Panel":
    st.title("🔐 Admin: Kelola Data Jemaat")

    # Inisialisasi login session
    if "admin_login" not in st.session_state:
        st.session_state["admin_login"] = False

    # Jika belum login, tampilkan form login
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

    # Jika sudah login, baru tampilkan tabs
    else:
        st.success("👋 Selamat datang Admin!")

        # Tabs navigasi admin
        tab1, tab2, tab3 = st.tabs(["🆕 Tambah Jemaat", "🖼️ Upload Foto", "📊 Statistik Presensi"])

    # ========== TAB 1: Tambah Jemaat ==========
    with tab1:
        st.markdown("### ✨ Tambah Jemaat Baru")
        delay = st.slider("⏱️ Tampilkan pesan sukses selama (detik):", 1, 5, 2)
    
        daftar_id = [j["ID"] for j in sheet_jemaat.get_all_records()]
        angka_terakhir = max([int(i[1:]) for i in daftar_id if i.startswith("J")], default=0)
        id_baru = f"J{angka_terakhir + 1:03d}"
    
        form_key = st.session_state.get("form_key", "form_jemaat_default")
        with st.form(key=form_key):
            st.text_input("ID Jemaat Baru", value=id_baru, disabled=True)
            nama_baru = st.text_input("Nama Jemaat Baru", key="input_nama")
            wa_baru = st.text_input("No WhatsApp (Contoh: 6281234567890)", key="input_wa")
            email_baru = st.text_input("Email Jemaat", key="input_email")
            simpan = st.form_submit_button("💾 Simpan")
    
        if simpan:
            error_msg = ""
    
            # Validasi nama tidak kosong
            if not nama_baru.strip():
                error_msg = "⚠️ Nama tidak boleh kosong."
    
            # Validasi nomor WhatsApp (angka, panjang, awalan 62)
            elif not re.fullmatch(r"62\d{8,15}", wa_baru.strip()):
                error_msg = "⚠️ Nomor WhatsApp tidak valid. Gunakan format seperti: 6281234567890 (tanpa spasi, tanpa +)."
    
            # Validasi email
            elif not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email_baru.strip()):
                error_msg = "⚠️ Alamat email tidak valid. Contoh: nama@email.com"
    
            if error_msg:
                st.warning(error_msg)
            else:
                sheet_jemaat.append_row([
                    id_baru,
                    nama_baru.strip(),
                    "",  # kolom file_id_foto
                    wa_baru.strip(),
                    email_baru.strip()
                ])
                # Kirim email
                sukses_email = kirim_email_selamat_datang(email_baru.strip(), nama_baru.strip())
        
                st.success(f"✅ Jemaat '{nama_baru}' berhasil ditambahkan dengan ID: {id_baru}")
                if sukses_email:
                    st.info(f"📧 Email selamat datang telah dikirim ke: {email_baru.strip()}")
                time.sleep(delay)
                st.session_state.form_key = f"form_{datetime.now().timestamp()}"
                st.experimental_rerun()

        # ========== TAB 2: Upload Foto ==========
        with tab2:
            st.markdown("### 🖼️ Upload Foto Jemaat")
            delay_foto = st.slider("⏱️ Lama tampil pesan sukses (detik)", 1, 5, 3, key="slider_foto")

            daftar_jemaat = sheet_jemaat.get_all_records()
            opsi_jemaat = {f"{j['Nama']} ({j['ID']})": j['ID'] for j in daftar_jemaat}

            selected = st.selectbox("Pilih Jemaat", options=list(opsi_jemaat.keys()), key="select_jemaat")
            foto_file = st.file_uploader("Pilih File Foto (JPG/PNG)", type=["jpg", "jpeg", "png"], key="upload_foto")

            if foto_file:
                st.image(foto_file, caption="📷 Preview Foto", width=150)

            if st.button("📤 Upload Foto"):
                if selected and foto_file:
                    from googleapiclient.discovery import build
                    from googleapiclient.http import MediaIoBaseUpload
                    from google.oauth2 import service_account

                    credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
                    drive_service = build("drive", "v3", credentials=credentials)

                    nama_file = f"foto_{opsi_jemaat[selected]}.jpg"
                    media = MediaIoBaseUpload(foto_file, mimetype="image/jpeg")
                    file_metadata = {
                        "name": nama_file,
                        "parents": [st.secrets["drive"]["folder_id_foto"]]
                    }
                    uploaded = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
                    file_id = uploaded.get("id")

                    baris_update = next(
                        i + 2 for i, row in enumerate(daftar_jemaat)
                        if row["ID"] == opsi_jemaat[selected]
                    )
                    sheet_jemaat.update_cell(baris_update, 3, file_id)

                    st.success(f"✅ Foto jemaat berhasil diunggah. ID File: {file_id}")
                    time.sleep(delay_foto)

                    for key in ["select_jemaat", "upload_foto", "slider_foto"]:
                        if key in st.session_state:
                            del st.session_state[key]

                    st.experimental_rerun()
                else:
                    st.warning("⚠️ Lengkapi pilihan jemaat dan foto terlebih dahulu.")

        # ========== TAB 3: Statistik Presensi + Logout ==========
        with tab3:
            st.markdown("### 📊 Statistik Presensi Global")

            df_presensi = sheet_presensi.get_all_records()
            st.metric("🧍 Total Presensi", len(df_presensi))

            tanggal_list = [r["Waktu"][:10] for r in df_presensi]
            st.bar_chart(Counter(tanggal_list))

            tanggal_filter = st.date_input("📅 Pilih Tanggal Presensi")
            tanggal_str = tanggal_filter.strftime("%Y-%m-%d")
            hasil_filter = [r for r in df_presensi if tanggal_str in r["Waktu"]]

            st.info(f"📌 Total Jemaat Hadir pada {tanggal_str}: {len(hasil_filter)}")
            st.dataframe(hasil_filter)

            import pandas as pd
            if st.download_button("⬇️ Export ke CSV", data=pd.DataFrame(hasil_filter).to_csv(index=False).encode("utf-8"),
                                  file_name=f"presensi_{tanggal_str}.csv", mime="text/csv"):
                st.success("✅ Berhasil diekspor.")

            if st.button("🔒 Logout Admin"):
                st.session_state["admin_login"] = False
                st.rerun()
                
