# ============================================
# PRESENSI JEMAAT STREAMLIT QR CAMERA (V3 + CAMERA MANUAL MODE + USB SCANNER MODE)
# ============================================

import streamlit as st
from PIL import Image
from pyzbar.pyzbar import decode
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date
from datetime import datetime
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time 
import locale
from zoneinfo import ZoneInfo
from reportlab.pdfgen import canvas
from io import BytesIO
from collections import Counter
import base64
import qrcode
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
from email.message import EmailMessage
import smtplib
import streamlit.components.v1 as components

# fungsi cache untuk semua sheet
@st.cache_data(ttl=60)
def load_data_jemaat():
    return sheet_jemaat.get_all_records()

@st.cache_data(ttl=60)
def load_data_ibadah():
    return sheet_ibadah.get_all_records()

@st.cache_data(ttl=60)
def load_data_presensi():
    return sheet_presensi.get_all_records()

# ===================== KONFIGURASI APLIKASI =====================
st.set_page_config(page_title="Presensi Jemaat", page_icon="🙏", layout="wide")

# =================== UI HEADER, BACKGROUND & FOOTER ===================
st.markdown("""
    <style>
        /* 🔆 BACKGROUND GRADASI WARNA */
        .stApp {
            background: linear-gradient(180deg, #FFFFFF, #FFFFFF, #0033FF); # Brand Color GPdI == #f9d423 (kuning), #ff4e50(merah), #007cf0(biru), #ffffff(putih) ==
            min-height: 100vh;
            background-attachment: fixed;
        }

        /* 🎯 HEADER */
        .header {
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: rgba(255, 255, 255, 0.9);
            padding: 1rem;
            border-bottom: 2px solid #ddd;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header img {
            height: 60px;
            margin-right: 20px;
        }
        .header h1 {
            font-size: 28px;
            color: #2c3e50;
            margin: 0;
        }

        /* 📝 FOOTER */
        .footer {
            position: fixed;
            bottom: 0;
            width: 100%;
            background-color: rgba(255, 255, 255, 0.8);
            text-align: left;
            padding: 0.5rem 1rem;
            color: #666;
            font-size: 13px;
            border-top: 1px solid #ccc;
        }
    </style>

    <div class="header">
        <img src="https://drive.google.com/thumbnail?id=1iMX_EgdFn6PcbllsAWezgyhypGymN1xE" alt="Logo Gereja">
        <h1>GPdI Pembaharuan Medan</h1>
    </div>
""", unsafe_allow_html=True)

# === HTML SLIDESHOW DAN LOGIKA IDLE ===
st.markdown("""
    <style>
        .slideshow {
            position: fixed;
            top: 80px;
            left: 0;
            width: 100%;
            height: 90vh;
            background-color: black;
            display: none;
            z-index: 9999;
            justify-content: center;
            align-items: center;
            flex-direction: column;
        }

        .slide-img {
            max-height: 80vh;
            max-width: 100%;
            object-fit: contain;
        }

        .slide-caption {
            color: white;
            font-size: 2rem;
            margin-top: 20px;
            text-align: center;
        }
    </style>

    <div class="slideshow" id="idleSlideShow">
        <img class="slide-img" id="slideImage" src="https://source.unsplash.com/featured/?cross" />
        <div class="slide-caption" id="slideCaption">"Selamat datang di Rumah Tuhan"</div>
    </div>

    <script>
        let idleTime = 0;
        let slides = [
            {img: "https://unsplash.com/photos/gray-cross-near-tall-green-trees-U_b-eSviHvs", caption: "Selamat datang di Rumah Tuhan"},
            {img: "https://source.unsplash.com/featured/?church", caption: "Tuhan itu baik, kasih setia-Nya selama-lamanya"},
            {img: "https://source.unsplash.com/featured/?worship", caption: "Masuklah gerbang-Nya dengan ucapan syukur"},
            {img: "https://source.unsplash.com/featured/?bible", caption: "Firman-Mu adalah pelita bagi kakiku"}
        ];
        let slideIndex = 0;

        function nextSlide() {
            slideIndex = (slideIndex + 1) % slides.length;
            document.getElementById("slideImage").src = slides[slideIndex].img;
            document.getElementById("slideCaption").textContent = slides[slideIndex].caption;
        }

        setInterval(function() {
            idleTime++;
            if (idleTime > 30) {
                document.getElementById("idleSlideShow").style.display = "flex";
            }
        }, 1000);

        document.addEventListener("mousemove", resetIdle);
        document.addEventListener("keydown", resetIdle);
        document.addEventListener("click", resetIdle);

        function resetIdle() {
            idleTime = 0;
            document.getElementById("idleSlideShow").style.display = "none";
        }

        setInterval(nextSlide, 5000);  // Ganti slide setiap 5 detik
    </script>
""", unsafe_allow_html=True)

# ===================== SIDEBAR NAVIGASI =====================
halaman = st.sidebar.selectbox("📂 Pilih Halaman", ["📸 Presensi Jemaat", "🔐 Admin Panel"])

# ===================== KONEKSI GOOGLE SHEETS =====================
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
client = gspread.authorize(creds)

sheet_presensi = client.open_by_key("1LI5D_rWMkek5CHnEbZgHW4BV_FKcS9TUP0icVlKK1kQ").worksheet("presensi")     #Ganti dengan key/ID Sheet dan nama sheet
sheet_jemaat = client.open_by_key("1LI5D_rWMkek5CHnEbZgHW4BV_FKcS9TUP0icVlKK1kQ").worksheet("data_jemaat")    #Ganti dengan key/ID Sheet dan nama sheet
sheet_ibadah = client.open_by_key("1LI5D_rWMkek5CHnEbZgHW4BV_FKcS9TUP0icVlKK1kQ").worksheet("Ibadah")         #Ganti dengan key/ID Sheet dan nama sheet

# ===================== FUNGSI KIRIM EMAIL =====================
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
        
# ===================== INISIALISASI SESSION STATE =====================
for k, v in {
    "reset_qr": False,
    "presensi_berhasil": False,
    "global_lock_time": 0,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ===================== FUNGSI PRESENSI =====================
def proses_presensi(qr_data):
    if time.time() - st.session_state["global_lock_time"] < 3:
        st.warning("⌛ Silakan tunggu sebentar sebelum melakukan presensi lagi...")
        return

    st.session_state["global_lock_time"] = time.time()

    daftar_jemaat = load_data_jemaat()
    qr_data = qr_data.strip()
    data_jemaat = next((j for j in daftar_jemaat if str(j["NIJ"]).strip() == qr_data), None)

    if not data_jemaat:
        st.error("🛑 NIJ tidak ditemukan dalam database.")
        return

    nama_jemaat = data_jemaat["Nama"]
    email_jemaat = data_jemaat.get("Email", "")
    foto_id = data_jemaat.get("File_ID_Foto", "").strip()

    waktu_wib = datetime.now(ZoneInfo("Asia/Jakarta"))
    waktu_str = waktu_wib.strftime("%d-%m-%Y %H:%M:%S")
    tanggal_hari_ini = waktu_wib.strftime("%d-%m-%Y")
    hari_indonesia = waktu_wib.strftime("%A")
    hari_mapping = {
        "Sunday": "Minggu", "Monday": "Senin", "Tuesday": "Selasa",
        "Wednesday": "Rabu", "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu"
    }
    hari_indonesia = hari_mapping.get(hari_indonesia, hari_indonesia)

    data_ibadah = load_data_ibadah()
    ibadah_hari_ini = [i for i in data_ibadah if i["Hari"].strip().lower() == hari_indonesia.lower()]

    if not ibadah_hari_ini:
        nama_ibadah = "Tidak Diketahui"
        jam_ibadah_obj = waktu_wib.replace(hour=10, minute=30)
    else:
        def waktu_ibadah_obj(i):
            jam_str = str(i["Jam"]).strip()
            hour, minute = map(int, jam_str.split(":"))
            return waktu_wib.replace(hour=hour, minute=minute, second=0, microsecond=0)
        ibadah_hari_ini.sort(key=lambda i: abs((waktu_ibadah_obj(i) - waktu_wib).total_seconds()))
        ibadah_terdekat = ibadah_hari_ini[0]
        nama_ibadah = ibadah_terdekat["Nama Ibadah"]
        jam_ibadah_obj = waktu_ibadah_obj(ibadah_terdekat)

    keterangan = "TEPAT WAKTU" if waktu_wib <= jam_ibadah_obj else "TERLAMBAT"

    riwayat = load_data_presensi()
    for r in riwayat:
        if r["NIJ"].strip() == qr_data and tanggal_hari_ini in r["Waktu"]:
            waktu_terakhir = r["Waktu"]
            st.warning(f"⚠️ Anda sudah melakukan presensi hari ini pada {waktu_terakhir}")
            return

    sheet_presensi.append_row([
        waktu_str, qr_data, nama_jemaat, keterangan, nama_ibadah
    ])

    st.success(f"📝 Kehadiran **{nama_jemaat}** sudah dicatat sebagai **{keterangan}** dalam **{nama_ibadah}** pada tanggal **{waktu_str}**!")

    warna_teks = "green" if keterangan == "TEPAT WAKTU" else "red"
    ikon = "✅" if keterangan == "TEPAT WAKTU" else "❌"

    st.markdown(f"""
    <div style="font-size:30px; font-weight:bold; color:{warna_teks}; text-align:center;">
        {ikon} {keterangan}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <audio autoplay>
        <source src="https://www.soundjay.com/buttons/sounds/beep-08b.mp3" type="audio/mpeg">
    </audio>
    """, unsafe_allow_html=True)

    if foto_id:
        foto_url = f"https://drive.google.com/thumbnail?id={foto_id}"
        st.image(foto_url, width=100, caption=f"🡭 Foto Jemaat: {nama_jemaat}")

    if email_jemaat:
        pesan_tambahan = (
            "Selamat datang di rumah Tuhan! Kami sangat menghargai kedatangan Saudara tepat waktu, "
            "karena hal ini menunjukkan rasa hormat kita kepada Tuhan dan kepada sesama jemaat. "
            "Mari kita bersama-sama memulai ibadah dengan hati yang tenang dan penuh sukacita."
        ) if keterangan == "TEPAT WAKTU" else (
            "Mari bersama-sama kita hadir tepat waktu dalam ibadah sebagai bentuk penghormatan kepada Tuhan "
            "dan persekutuan yang kudus. Keterlambatan dapat mengurangi hadirat Tuhan dan menghalangi kita "
            "untuk sepenuhnya terlibat dalam penyembahan."
        )

        body_email = (
            f"Syalom Bapak/Ibu/Saudara {nama_jemaat},\n\n"
            f"Presensi Anda pada {waktu_str} telah tercatat sebagai *{keterangan}* dalam *{nama_ibadah}*.\n\n"
            f"{pesan_tambahan}\n\n"
            "Tuhan Yesus Memberkati 🙏\n\n-- IT & Media GPdI Pembaharuan."
        )

        kirim_email(email_jemaat, "Kehadiran Jemaat GPdI Pembaharuan", body_email)

    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(100, 750, "SERTIFIKAT KEHADIRAN JEMAAT")
    c.setFont("Helvetica", 12)
    c.drawString(100, 700, f"Nama Jemaat              : {nama_jemaat}")
    c.drawString(100, 680, f"NIJ (Nomor Induk Jemaat) : {qr_data}")
    c.drawString(100, 660, f"Waktu Hadir              : {waktu_str}")
    c.drawString(100, 640, f"Jenis Ibadah             : {nama_ibadah}")
    c.drawString(100, 620, f"Keterangan               : {keterangan}")
    c.drawString(100, 600, "Lokasi                   : GPdI Pembaharuan Medan")
    c.save()
    buffer.seek(0)
    st.download_button("📅 Download Sertifikat Kehadiran", buffer, f"sertifikat_{qr_data}.pdf", "application/pdf")

    # Tandai bahwa presensi sukses → agar halaman reload untuk clear form
    st.session_state["presensi_berhasil"] = True

# ===================== HALAMAN PRESENSI =====================
if halaman == "📸 Presensi Jemaat":
    st.title("Sistem Absensi Jemaat")
    st.markdown("### 🖨️ Arahkan QR Code ke Scanner USB")

    # ✅ Autofokus JS
    components.html("""
    <script>
    window.requestAnimationFrame(() => {
        const inputs = window.parent.document.querySelectorAll('input');
        for (let i = 0; i < inputs.length; i++) {
            if (inputs[i].placeholder === "Scan QR di sini...") {
                inputs[i].focus();
                break;
            }
        }
    });
    </script>
    """, height=0)

    # 🧾 Input QR (gunakan widget value sekali saja)
    qr_code_input = st.text_input(
        label="🆔 NIJ dari QR Code",
        placeholder="Scan QR di sini...",
        key="input_qr",
        label_visibility="collapsed"
    )

    # ⛳ Proses QR
    if qr_code_input:
        proses_presensi(qr_code_input)

    # 🔁 Jika presensi berhasil, reload halaman
    if st.session_state["presensi_berhasil"]:
        st.session_state["presensi_berhasil"] = False
        components.html("""
        <script>
        setTimeout(() => window.parent.location.reload(), 3000);
        </script>
        """, height=0)

    # ========== MODE KAMERA MANUAL ==========
    st.markdown("### 📷 Gunakan Kamera Manual (Opsional)")
    if "kamera_manual_aktif" not in st.session_state:
        st.session_state.kamera_manual_aktif = False

    if not st.session_state.kamera_manual_aktif:
        if st.button("Aktifkan Kamera Manual"):
            st.session_state.kamera_manual_aktif = True
            st.experimental_rerun()

    if st.session_state.kamera_manual_aktif:
        with st.form("kamera_manual_form"):
            img = st.camera_input("📸 Ambil Gambar QR Code dari Kamera")
            col1, col2 = st.columns([1, 1])
            with col1:
                submit_camera = st.form_submit_button("✅ Proses dari Kamera")
            with col2:
                nonaktif = st.form_submit_button("❌ Nonaktifkan Kamera")

        if nonaktif:
            st.session_state.kamera_manual_aktif = False
            st.experimental_rerun()

        if submit_camera and img:
            from pyzbar.pyzbar import decode
            image = Image.open(img)
            decoded = decode(image)
            if decoded:
                qr_data_camera = decoded[0].data.decode("utf-8")
                st.info(f"✅ QR Terdeteksi: {qr_data_camera}")
                proses_presensi(qr_data_camera)
            else:
                st.error("❌ QR Code tidak terbaca dari gambar. Silakan ulangi scan.")

# ===================== HALAMAN ADMIN PANEL =====================
elif halaman == "🔐 Admin Panel":
    st.header("🔐 Manajemen Jemaat")

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
            st.markdown("Gunakan tab di bawah ini.")

        with col2:
            if st.button("🔒 Logout"):
                st.session_state["admin_login"] = False
                st.rerun()

        # Tabs Admin
        tab1, tab2, tab3, tab4 = st.tabs(["🆕 Tambah Jemaat", "🖼️ Upload Foto", "📊 Statistik Presensi", "🏠 Tambah Ibadah"])
        
        # Defenisikan fungsi menghasilkan NIJ Otomatis
        def generate_nij(nik, gender, id_baru):
            nik_part = nik[6:12]  # Ambil 6 digit tengah dari NIK
            gender_code = "01" if gender.lower() == "laki-laki" else "02"
            bulan_daftar = datetime.now().strftime("%m")
            tahun_daftar = datetime.now().strftime("%y")
        
            angka_id = f"{int(id_baru[1:]):04d}"  # Hilangkan huruf 'J', jadikan angka 4 digit
            base = f"{nik_part}-{gender_code}{bulan_daftar}{tahun_daftar}-{angka_id}"
            return base

        # ========== TAB 1: Tambah Jemaat ==========
        with tab1:
            st.markdown("### ✨ Tambah Jemaat Baru")
            delay = st.slider("⏱️ Tampilkan pesan sukses selama (detik):", 1, 5, 2)
        
           # --- Load data jemaat dan buat ID baru ---
            daftar_jemaat = load_data_jemaat()

            # Buat ID baru
            daftar_id = [j["ID"] for j in daftar_jemaat]
            angka_terakhir = max([int(i[1:]) for i in daftar_id if i.startswith("J")], default=0)
            id_baru = f"J{angka_terakhir + 1:03d}"
            
            # --- Inisialisasi session state (jika belum ada) ---
            for key in ["nik", "nama_baru", "no_wa", "email_baru"]:
                if key not in st.session_state:
                    st.session_state[key] = ""
            
            # --- Fungsi Validasi ---
            def is_valid_nik(nik):
                return bool(re.fullmatch(r'\d{16}', nik))
            
            def is_valid_wa(no):
                return bool(re.match(r"^628\d{7,10}$", no))
            
            def is_valid_email(email):
                return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email))
            
            # --- Validasi Real-time ---
            def show_validation_icon(is_valid):
                if is_valid:
                    st.markdown("✅", unsafe_allow_html=True)
                else:
                    st.markdown("❌", unsafe_allow_html=True)
            
            # --- Formulir Utama ---
            form_key = st.session_state.get("form_key", "form_jemaat_default")
            with st.form(key=form_key):
                st.text_input("ID Jemaat", value=id_baru, disabled=True)
            
                # Kolom NIK (Hanya angka, real-time validasi)
                nik = st.text_input("NIK", max_chars=16, key="nik")
                nik_clean = ''.join(filter(str.isdigit, nik))
                if nik != nik_clean:
                    st.session_state["nik"] = nik_clean
                    st.rerun()
                col1, col2 = st.columns([0.9, 0.1])
                with col1:
                    pass  # Biarkan input di atas
                with col2:
                    show_validation_icon(is_valid_nik(nik_clean))
            
                # Nama
                nama_baru = st.text_input("Nama Lengkap", key="nama_baru")
            
                # Jenis Kelamin
                jenis_kelamin = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
            
                # Tanggal Lahir + Usia
                tgl_lahir = st.date_input("Tanggal Lahir", min_value=date(1900,1,1), max_value=date.today(), value=date(2025,1,1))
                today = date.today()
                usia_delta = relativedelta(today, tgl_lahir)
                usia_str = f"{usia_delta.years} Tahun, {usia_delta.months} Bulan, {usia_delta.days} Hari"
                st.text(f"Usia otomatis: {usia_str}")
            
                # Nomor WA
                no_wa = st.text_input("No WhatsApp (format 628xxx)", key="no_wa")
                col1, col2 = st.columns([0.9, 0.1])
                with col1:
                    pass
                with col2:
                    show_validation_icon(is_valid_wa(no_wa))
            
                # Email
                email_baru = st.text_input("Email aktif", key="email_baru")
                col1, col2 = st.columns([0.9, 0.1])
                with col1:
                    pass
                with col2:
                    show_validation_icon(is_valid_email(email_baru))
            
                # Tombol Simpan
                simpan = st.form_submit_button("💾 Simpan")
            
            # --- Setelah Klik Simpan ---
            if simpan:
                nik = nik.strip()
                nama_baru = nama_baru.strip()
                no_wa = no_wa.strip()
                email_baru = email_baru.strip()
            
                if not nik or not nama_baru or not no_wa or not email_baru:
                    st.warning("⚠️ Semua isian wajib diisi.")
                elif not is_valid_nik(nik):
                    st.error("❌ NIK harus 16 digit.")
                elif not is_valid_wa(no_wa):
                    st.error("❌ Format nomor WhatsApp tidak valid.")
                elif not is_valid_email(email_baru):
                    st.error("❌ Format email tidak valid.")
                elif any(str(j["NIK"]).strip() == nik for j in daftar_jemaat):
                    st.error("❌ NIK sudah terdaftar.")
                elif any(str(j["No_WhatsApp"]).strip() == no_wa for j in daftar_jemaat):
                    st.error("❌ Nomor WhatsApp sudah terdaftar.")
                elif any(str(j["Email"]).strip().lower() == email_baru.lower() for j in daftar_jemaat):
                    st.error("❌ Email sudah terdaftar.")
                else:
                    nij = generate_nij(nik, jenis_kelamin, id_baru)
                    tgl_lahir_str = tgl_lahir.strftime("%d-%m-%Y")
            
                    # Simpan data ke sheet
                    sheet_jemaat.append_row([
                        id_baru,               # ID
                        nik,                   # NIK
                        nij,                   # NIJ
                        nama_baru.strip(),     # Nama
                        jenis_kelamin,         # Jenis Kelamin
                        tgl_lahir_str,         # Tgl Lahir
                        usia_str,              # Usia lengkap
                        "", "", "",            # File_KTP, File_KK, File_ID_Foto
                        no_wa.strip(),         # No WhatsApp
                        email_baru.strip(),    # Email
                        ""                     # QR Code
                    ])
            
                    st.success(f"✅ Jemaat '{nama_baru}' berhasil ditambahkan dengan NIJ: {nij}")
            
                    # Reset kolom input
                    for key in ["nik", "nama_baru", "no_wa", "email_baru"]:
                        st.session_state[key] = ""
            
                    st.rerun()

                    # Kirim email selamat datang (jika email diisi)
                    if email_baru.strip():
                        import smtplib
                        from email.mime.text import MIMEText

                        msg = MIMEText(f"Syalom {nama_baru},\n\nSelamat datang di sistem presensi jemaat GPdI Pembaharuan.\n\nNIJ Anda: {nij}\n\nGunakan kartu atau QR Code Anda saat hadir di ibadah.\n\nTuhan Yesus Memberkati 🙏. \n\n-- IT & Media GPdI Pembaharuan.")
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
                    st.rerun()
        # ========== TAB 2: Upload Foto ==========
        with tab2:
            st.markdown("### 🖼️ Upload Foto dan Dokumen Jemaat")
        
            delay_foto = st.slider("⏱️ Lama tampil pesan sukses (detik)", 1, 5, 3, key="slider_foto")
            daftar_jemaat = load_data_jemaat()
            opsi_jemaat = {f"{j['Nama']} ({j['ID']})": j['ID'] for j in daftar_jemaat}
        
            selected = st.selectbox("Pilih Jemaat", options=list(opsi_jemaat.keys()), key="select_jemaat")
            jemaat_id = opsi_jemaat[selected]
            jemaat_data = next(j for j in daftar_jemaat if j["ID"] == jemaat_id)
            baris_update = next(i + 2 for i, row in enumerate(daftar_jemaat) if row["ID"] == jemaat_id)
        
            foto_file = st.file_uploader("📷 Upload Foto Jemaat (JPG/PNG)", type=["jpg", "jpeg", "png"], key="upload_foto")
            ktp_file = st.file_uploader("🪪 Upload File KTP (JPG/PNG)", type=["jpg", "jpeg", "png"], key="ktp_file")
            kk_file = st.file_uploader("🏠 Upload File KK (JPG/PNG)", type=["jpg", "jpeg", "png"], key="kk_file")
        
            # ========== PREVIEW FILE ==========
            cols = st.columns(3)
            if foto_file:
                cols[0].image(foto_file, caption="📷 Foto", width=100)
            if ktp_file:
                cols[1].image(ktp_file, caption="🪪 KTP", width=100)
            if kk_file:
                cols[2].image(kk_file, caption="🏠 KK", width=100)
        
            # Fungsi Upload
            def upload_and_overwrite(file_data, nama_file, folder_id):
                from googleapiclient.discovery import build
                from googleapiclient.http import MediaIoBaseUpload
                from google.oauth2 import service_account
        
                credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
                drive_service = build("drive", "v3", credentials=credentials)
        
                # Cari file lama dengan nama yang sama
                query = f"name = '{nama_file}' and '{folder_id}' in parents and trashed = false"
                results = drive_service.files().list(q=query, fields="files(id)").execute()
                existing_files = results.get("files", [])
        
                # Hapus file lama
                for f in existing_files:
                    drive_service.files().delete(fileId=f["id"]).execute()
        
                # Upload file baru
                media = MediaIoBaseUpload(file_data, mimetype="image/jpeg")
                uploaded = drive_service.files().create(
                    body={"name": nama_file, "parents": [folder_id]},
                    media_body=media,
                    fields="id"
                ).execute()
                return uploaded["id"]
        
            # ========== UPLOAD ==========
            if st.button("📤 Upload Semua File"):
                if not (foto_file and ktp_file and kk_file):
                    st.warning("⚠️ Semua file (Foto, KTP, KK) wajib diunggah sebelum melanjutkan.")
                    st.stop()
        
                # Notifikasi jika file sebelumnya sudah ada
                if jemaat_data.get("File_ID_Foto"):
                    st.warning("⚠️ Foto sudah pernah diunggah. File akan ditimpa.")
                if jemaat_data.get("File_KTP"):
                    st.warning("⚠️ File KTP sudah pernah diunggah. File akan ditimpa.")
                if jemaat_data.get("File_KK"):
                    st.warning("⚠️ File KK sudah pernah diunggah. File akan ditimpa.")
        
                # FOTO
                nama_foto = f"foto_{jemaat_id}.jpg"
                file_id_foto = upload_and_overwrite(foto_file, nama_foto, st.secrets["drive_foto"]["folder_id_foto"])
                sheet_jemaat.update_cell(baris_update, 10, file_id_foto)
        
                # KTP
                nama_ktp = f"ktp_{jemaat_id}.jpg"
                file_id_ktp = upload_and_overwrite(ktp_file, nama_ktp, st.secrets["drive_foto"]["folder_id_ktp"])
                link_ktp = f'=HYPERLINK("https://drive.google.com/file/d/{file_id_ktp}"; "Lihat KTP")'
                sheet_jemaat.update_cell(baris_update, 8, link_ktp)
        
                # KK
                nama_kk = f"kk_{jemaat_id}.jpg"
                file_id_kk = upload_and_overwrite(kk_file, nama_kk, st.secrets["drive_foto"]["folder_id_kk"])
                link_kk = f'=HYPERLINK("https://drive.google.com/file/d/{file_id_kk}"; "Lihat KK")'
                sheet_jemaat.update_cell(baris_update, 9, link_kk)
        
                st.success("✅ Semua file berhasil diunggah dan disimpan ke database.")
        
                # Reset form
                for key in ["select_jemaat", "upload_foto", "ktp_file", "kk_file", "slider_foto"]:
                    if key in st.session_state:
                        del st.session_state[key]
                time.sleep(delay_foto)
                st.experimental_rerun()
        
            # ========== TOMBOL BERSIHKAN ==========
            if st.button("🧹 Bersihkan Form"):
                for key in ["select_jemaat", "upload_foto", "ktp_file", "kk_file", "slider_foto"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.experimental_rerun()

        # ========== TAB 3: Statistik Presensi ==========
        with tab3:
            st.markdown("### 📊 Statistik Presensi")
        
            df_presensi = load_data_presensi()
            if not df_presensi:
                st.warning("Belum ada data presensi.")
                st.stop()
        
            import pandas as pd
            from datetime import datetime
        
            df = pd.DataFrame(df_presensi)
            df["Tanggal"] = pd.to_datetime(df["Waktu"].str[:10], format="%d-%m-%Y")
        
            # 🌍 Filter Ibadah/Lokasi
            if "Ibadah" in df.columns:
                ibadah_opsi = sorted(df["Ibadah"].dropna().unique())
                ibadah_pilih = st.selectbox("🙏 Pilih Jenis Ibadah / Lokasi", ["Semua"] + ibadah_opsi)
                if ibadah_pilih != "Semua":
                    df = df[df["Ibadah"] == ibadah_pilih]
            else:
                st.warning("⚠️ Kolom 'Ibadah' tidak ditemukan di data presensi.")
        
            # ========= FILTER TAHUN / BULAN / TANGGAL =========
            tahun_opsi = sorted(df["Tanggal"].dt.year.unique(), reverse=True)
            tahun_pilih = st.selectbox("🗓️ Pilih Tahun", tahun_opsi)
        
            df_tahun = df[df["Tanggal"].dt.year == tahun_pilih]
        
            bulan_opsi = sorted(df_tahun["Tanggal"].dt.month.unique())
            bulan_nama = {
                1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
                7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
            }
            bulan_pilih = st.selectbox("📅 Pilih Bulan", bulan_opsi, format_func=lambda x: bulan_nama[x])
            df_bulan = df_tahun[df_tahun["Tanggal"].dt.month == bulan_pilih]
        
            tanggal_opsi = sorted(df_bulan["Tanggal"].dt.day.unique())
            tanggal_pilih = st.selectbox("📍 Pilih Tanggal", tanggal_opsi)
            tanggal_final = datetime(tahun_pilih, bulan_pilih, tanggal_pilih)
            df_tanggal = df_bulan[df_bulan["Tanggal"].dt.day == tanggal_pilih]
        
            # Format Bahasa Indonesia
            def format_tanggal_indonesia(dt):
                hari_dict = {
                    "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
                    "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu",
                    "Sunday": "Minggu"
                }
                bulan_dict = {
                    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
                    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
                    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
                }
                hari = hari_dict[dt.strftime("%A")]
                tanggal = dt.day
                bulan = bulan_dict[dt.month]
                tahun = dt.year
                return f"{hari}, {tanggal} {bulan} {tahun}"
        
            st.markdown(f"#### ✅ Total Jemaat Hadir pada **{format_tanggal_indonesia(tanggal_final)}**: {len(df_tanggal)}")
        
            # 🔢 Tampilkan Jumlah Per Jenis Ibadah
            ibadah_count = df_bulan.groupby("Ibadah")["Nama"].count().reset_index(name="Jumlah Hadir")
            st.markdown("#### 🙌 Jumlah Kehadiran per Ibadah (Bulan Ini)")
            st.dataframe(ibadah_count)
        
            # ========= GRAFIK TREN =========
            col1, col2, col3 = st.columns(3)
        
            # Grafik Mingguan
            mingguan = df_bulan.copy()
            mingguan["Minggu Ke"] = mingguan["Tanggal"].dt.isocalendar().week
            mingguan_count = mingguan.groupby("Minggu Ke")["Nama"].count().reset_index(name="Jumlah")
            with col1:
                st.markdown("##### 📆 Grafik Mingguan")
                st.bar_chart(mingguan_count.set_index("Minggu Ke"))
        
            # Grafik Bulanan
            bulanan = df[df["Tanggal"].dt.year == tahun_pilih].copy()
            bulanan["Bulan"] = bulanan["Tanggal"].dt.month.map(bulan_nama)
            bulanan_count = bulanan.groupby("Bulan")["Nama"].count().reindex(bulan_nama.values()).dropna().reset_index(name="Jumlah")
            with col2:
                st.markdown("##### 📅 Grafik Bulanan")
                st.bar_chart(bulanan_count.set_index("Bulan"))
        
            # Grafik Tahunan
            tahunan = df.copy()
            tahunan["Tahun"] = tahunan["Tanggal"].dt.year
            tahunan_count = tahunan.groupby("Tahun")["Nama"].count().reset_index(name="Jumlah")
            with col3:
                st.markdown("##### 📊 Grafik Tahunan")
                st.bar_chart(tahunan_count.set_index("Tahun"))
        
            # ========= Tabel Presensi Detail =========
            st.markdown("### 📋 Tabel Kehadiran (Tanggal Terpilih)")
            st.dataframe(df_tanggal)
        
            # Export CSV
            st.download_button("⬇️ Export CSV", data=df_tanggal.to_csv(index=False).encode("utf-8"),
                               file_name=f"presensi_{tanggal_final.strftime('%d%m%Y')}.csv", mime="text/csv")
       
        # ========== TAB 4: Tambah Ibadah ==========
        with tab4:
            st.markdown("### ➕ Tambah atau Edit Jenis Ibadah")
            sheet_ibadah = client.open_by_key("1LI5D_rWMkek5CHnEbZgHW4BV_FKcS9TUP0icVlKK1kQ").worksheet("Ibadah")
            data_lama = load_data_ibadah()
            df_ibadah = pd.DataFrame(data_lama)
        
            # ========== TAMBAH / EDIT FORM ==========
            mode = st.radio("📌 Mode Operasi", ["Tambah", "Edit"], horizontal=True)
        
            if mode == "Tambah":
                with st.form("form_tambah_ibadah"):
                    nama_ibadah = st.text_input("🕊️ Nama Ibadah")
                    lokasi_ibadah = st.text_input("🏠 Lokasi Ibadah")
                    hari_ibadah = st.selectbox("📅 Hari Ibadah", [
                        "Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Setiap Hari"
                    ])
                    jam_ibadah = st.time_input("⏰ Jam Ibadah")
                    keterangan = st.text_area("📝 Keterangan Tambahan")
                    submit_ibadah = st.form_submit_button("💾 Simpan Ibadah")
        
                if submit_ibadah:
                    nama_bersih = nama_ibadah.strip()
                    if not nama_bersih:
                        st.warning("⚠️ Nama ibadah wajib diisi.")
                    elif nama_bersih in [r["Nama Ibadah"].strip() for r in data_lama]:
                        st.error(f"❌ Ibadah '{nama_bersih}' sudah ada.")
                    else:
                        nomor_terakhir = len(data_lama) + 1
                        kode_baru = f"IBD-{nomor_terakhir:03d}"
        
                        sheet_ibadah.append_row([
                            nomor_terakhir,
                            kode_baru,
                            nama_bersih,
                            lokasi_ibadah.strip(),
                            hari_ibadah,
                            jam_ibadah.strftime("%H:%M"),
                            keterangan.strip()
                        ])
                        st.success(f"✅ Ibadah '{nama_bersih}' berhasil ditambahkan dengan kode {kode_baru}.")
                        st.experimental_rerun()
        
            # ========== MODE EDIT ==========
            if mode == "Edit" and not df_ibadah.empty:
                pilih = st.selectbox("✏️ Pilih Ibadah untuk Diedit", df_ibadah["Nama Ibadah"])
                row_edit = df_ibadah[df_ibadah["Nama Ibadah"] == pilih].iloc[0]
                idx = df_ibadah[df_ibadah["Nama Ibadah"] == pilih].index[0]
        
                with st.form("form_edit_ibadah"):
                    nama_ibadah = st.text_input("🕊️ Nama Ibadah", value=row_edit["Nama Ibadah"])
                    lokasi_ibadah = st.text_input("🏠 Lokasi Ibadah", value=row_edit["Lokasi"])
                    hari_ibadah = st.selectbox("📅 Hari Ibadah", [
                        "Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Setiap Hari"
                    ], index=["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Setiap Hari"].index(row_edit["Hari"]))
                    jam_ibadah = st.time_input("⏰ Jam Ibadah", value=datetime.strptime(row_edit["Jam"], "%H:%M").time())
                    keterangan = st.text_area("📝 Keterangan Tambahan", value=row_edit["Keterangan"])
                    submit_edit = st.form_submit_button("✅ Update Ibadah")
        
                if submit_edit:
                    sheet_ibadah.update(f"C{idx+2}:G{idx+2}", [[
                        nama_ibadah.strip(),
                        lokasi_ibadah.strip(),
                        hari_ibadah,
                        jam_ibadah.strftime("%H:%M"),
                        keterangan.strip()
                    ]])
                    st.success(f"✅ Data ibadah '{nama_ibadah}' berhasil diperbarui.")
                    st.experimental_rerun()
        
            # ========== TABEL DAFTAR IBADAH ==========
            st.markdown("### 📋 Daftar Ibadah")
            df_ibadah = pd.DataFrame(load_data_ibadah())
            st.dataframe(df_ibadah)
        
            # ========== HAPUS IBADAH ==========
            st.markdown("### 🗑️ Hapus Ibadah")
            # Pilihan hapus
            nama_opsi = [r["Nama Ibadah"] for r in data_lama]
            ibadah_hapus = st.selectbox("🗑️ Pilih Ibadah untuk Dihapus", nama_opsi)
            hapus = st.button("🗑️ Hapus Ibadah Ini")
            
            if hapus:
                index = next((i for i, r in enumerate(data_lama, start=2) if r["Nama Ibadah"] == ibadah_hapus), None)
                if index:
                    sheet_ibadah.delete_rows(index)  # ✅ Panggil dengan "s"
                    st.success(f"✅ Ibadah '{ibadah_hapus}' berhasil dihapus.")
                    st.experimental_rerun()
                else:
                    st.warning("⚠️ Tidak ditemukan baris untuk dihapus.")
                    st.experimental_rerun()

# ===================== FOOTER =====================
st.markdown("""
    <div class="footer">
        © 2025 GPdI Pembaharuan Medan — IT & Media Ministry
    </div>
""", unsafe_allow_html=True)
