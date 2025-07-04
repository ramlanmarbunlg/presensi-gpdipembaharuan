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
import smtplib
from email.message import EmailMessage

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

# ===================== FUNGSI KIRIM EMAIL (BERHASIL PRESENSI) =====================
def kirim_email(to_email, subject, body):
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = st.secrets["email_smtp"]["sender"]
        msg["To"] = to_email
        msg.set_content(body)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(st.secrets["email_smtp"]["sender"], st.secrets["email_smtp"]["app_password"])
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
                st.success(f"📝 Kehadiran {nama_jemaat} berhasil dicatat pada sistem!")

                if foto_id:
                    foto_url = f"https://drive.google.com/thumbnail?id={foto_id}"
                    try:
                        st.image(foto_url, width=200, caption=f"🡭 Foto Jemaat: {nama_jemaat}")
                    except:
                        st.warning("⚠️ Gagal memuat foto jemaat.")

                # Kirim email ke jemaat
                if email_jemaat:
                    kirim_email(email_jemaat, "Kehadiran Jemaat GPdI Pembaharuan", f"Syalom {nama_jemaat},\n\nPresensi Anda pada {waktu_str} telah tercatat di sistem GPdI Pembaharuan!\n\nTuhan Yesus Memberkati 🙏\n\n-- Admin GPdI Pembaharuan.")

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

    # SIDEBAR LOGOUT – Opsi 1
    with st.sidebar:
        if st.session_state.get("admin_login", False):
            st.markdown("---")
            if st.button("🔒 Logout Admin"):
                st.session_state["admin_login"] = False
                st.rerun()

    # Login Form jika belum login
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

    # ====== Jika berhasil login admin ======
    else:
        # Opsi 2: Logout Button di Header (Atas Tabs)
        st.markdown("### 👋 Selamat datang Admin!")

        col1, col2 = st.columns([6, 1])
        with col1:
            st.markdown("Kelola data jemaat menggunakan tab di bawah ini.")

        with col2:
            if st.button("🔒 Logout"):
                st.session_state["admin_login"] = False
                st.rerun()

        # Tabs Admin
        tab1, tab2, tab3 = st.tabs(["🆕 Tambah Jemaat", "🖼️ Upload Foto", "📊 Statistik Presensi"])

        # ========== TAB 1: Tambah Jemaat ==========
        with tab1:
            st.markdown("### ✨ Tambah Jemaat Baru")
            delay = st.slider("⏱️ Tampilkan pesan sukses selama (detik):", 1, 5, 2)
        
            # Ambil semua data jemaat
            daftar_jemaat = sheet_jemaat.get_all_records()
        
            # Buat ID baru
            daftar_id = [j["ID"] for j in daftar_jemaat]
            angka_terakhir = max([int(i[1:]) for i in daftar_id if i.startswith("J")], default=0)
            id_baru = f"J{angka_terakhir + 1:03d}"
        
            form_key = st.session_state.get("form_key", "form_jemaat_default")
            with st.form(key=form_key):
                st.text_input("ID Jemaat", value=id_baru, disabled=True)
                nik = st.text_input("NIK", max_chars=20)
                nama_baru = st.text_input("Nama Lengkap")
                jenis_kelamin = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
                no_wa = st.text_input("No WhatsApp (format 08xxxx / 628xxx)")
                email_baru = st.text_input("Email")
                simpan = st.form_submit_button("💾 Simpan")
        
            # Fungsi validasi regex
            def is_valid_wa(no):
                import re #untuk validasi no WA
                # Valid: 08xxxxxxxxxx (10–12 digit) atau 628xxxxxxxxx
                wa_regex = r"^(08\d{8,11}|628\d{7,10})$"
                return re.match(wa_regex, no)
        
            def is_valid_email(email):
                import re #untuk validasi email
                email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
                return re.match(email_regex, email)
        
            # Jika tombol simpan ditekan
            if simpan:
                if not nik.strip() or not nama_baru.strip() or not no_wa.strip() or not email_baru.strip():
                    st.warning("⚠️ Semua field wajib diisi.")
                elif not is_valid_wa(no_wa.strip()):
                    st.error("❌ Format nomor WhatsApp tidak valid (harus 10-13 digit).")
                elif not is_valid_email(email_baru.strip()):
                    st.error("❌ Format email tidak valid.")
                elif any(j["NIK"] == nik for j in daftar_jemaat):
                    st.error("❌ NIK sudah terdaftar.")
                elif any(j["Email"].lower() == email_baru.lower() for j in daftar_jemaat):
                    st.error("❌ Email sudah digunakan.")
                elif any(j["No_WhatsApp"] == no_wa for j in daftar_jemaat):
                    st.error("❌ Nomor WhatsApp sudah digunakan.")
                else:
                    # Simpan ke Sheet sesuai urutan kolom
                    sheet_jemaat.append_row([
                        id_baru,              # A: ID
                        nik,                  # B: NIK
                        nama_baru.strip(),    # C: Nama
                        jenis_kelamin,        # D: Jenis Kelamin
                        "",                   # E: File_ID_Foto (kosong dulu)
                        no_wa.strip(),        # F: No_WhatsApp
                        email_baru.strip(),   # G: Email
                        ""                    # H: QR (kosong dulu)
                    ])
        
                    st.success(f"✅ Jemaat '{nama_baru}' berhasil ditambahkan dengan ID: {id_baru}")

                    # Kirim email selamat datang (jika email diisi)
                    if email_baru.strip():
                        import smtplib
                        from email.mime.text import MIMEText

                        msg = MIMEText(f"Syalom {nama_baru},\n\nSelamat datang di sistem presensi jemaat GPdI Pembaharuan.\n\nID Jemaat Anda: {id_baru}\n\nGunakan kartu atau QR Code Anda saat hadir di ibadah.\n\nTuhan Yesus Memberkati 🙏. \n\n-- Admin GPdI Pembaharuan.")
                        msg["Subject"] = "Selamat Datang di GPdI Pembaharuan"
                        msg["From"] = st.secrets["email_smtp"]["sender"]
                        msg["To"] = email_baru

                        try:
                            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                                server.starttls()
                                server.login(st.secrets["email_smtp"]["sender"], st.secrets["email_smtp"]["app_password"])
                                server.send_message(msg)
                            st.success("📧 Email selamat datang berhasil dikirim.")
                        except Exception as e:
                            st.warning(f"⚠️ Gagal mengirim email: {e}")

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

        # ========== TAB 3: Statistik Presensi ==========
        with tab3:
            st.markdown("### 📊 Statistik Presensi")
            df_presensi = sheet_presensi.get_all_records()
            st.metric("🧍 Total Presensi", len(df_presensi))

            tanggal_list = [r["Waktu"][:10] for r in df_presensi]
            st.bar_chart(Counter(tanggal_list))

            # Filter presensi per tanggal
            tanggal_filter = st.date_input("📅 Pilih Tanggal Presensi")
            tanggal_str = tanggal_filter.strftime("%Y-%m-%d")
            hasil_filter = [r for r in df_presensi if tanggal_str in r["Waktu"]]

            st.info(f"📌 Total Jemaat Hadir pada {tanggal_str}: {len(hasil_filter)}")
            st.dataframe(hasil_filter)

            # Ekspor CSV
            import pandas as pd
            def convert_to_csv(data): return pd.DataFrame(data).to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Export ke CSV", data=convert_to_csv(hasil_filter),
                               file_name=f"presensi_{tanggal_str}.csv", mime="text/csv")

                
