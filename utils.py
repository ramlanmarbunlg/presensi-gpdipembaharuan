from datetime import date, datetime
import smtplib
from email.message import EmailMessage
import streamlit as st
import logging

# Setup logger (untuk logging alternatif)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def load_data_jemaat():
    data = st.session_state.get("data_jemaat", [])
    if not isinstance(data, list):
        st.warning("Data jemaat tidak dalam format list.")
        logger.warning("Data jemaat bukan list. Ditemukan: %s", type(data))
        return []
    return data

def parse_tanggal_lahir(tgl_str):
    if not tgl_str or tgl_str.strip() == "":
        return None  # kosong, jangan parse
    try:
        return datetime.strptime(tgl_str.strip(), "%d-%m-%Y").date()
    except Exception as e:
        st.warning(f"Gagal parsing tanggal: '{tgl_str}' | Error: {e}")
        logger.warning("Gagal parsing tanggal: '%s' | Error: %s", tgl_str, e)
        return None

def filter_ulang_tahun_hari_ini():
    today = date.today()
    jemaat = load_data_jemaat()
    hasil = []
    
    valid = 0
    invalid = 0

    for j in jemaat:
        tgl_lahir_raw = j.get("Tgl Lahir", "").strip()
        parsed = parse_tanggal_lahir(tgl_lahir_raw)

        if parsed:
            valid += 1
            if parsed.day == today.day and parsed.month == today.month:
                hasil.append(j)
        else:
            invalid += 1

    st.info(f"📊 Tanggal valid: {valid}, Tanggal tidak valid/kosong: {invalid}")
    logger.info("Jumlah tanggal valid: %d, tidak valid/kosong: %d", valid, invalid)
    return hasil

def kirim_email_ultah(nama, email_penerima, usia):
    if not email_penerima:
        st.warning(f"Alamat email kosong untuk {nama}")
        logger.warning("Email kosong saat mengirim ke: %s", nama)
        return False

    sender = st.secrets["email_smtp"]["sender"]
    password = st.secrets["email_smtp"]["app_password"]

    subject = f"🎉 Selamat Ulang Tahun, {nama}!"
    body = (
        f"Syalom {nama},\n\n"
        f"Gembala, Pelayan dan Jemaat mengucapkan SELAMAT ULANG TAHUN! 🎂 yang ke- {usia}\n\n"
        "Pada hari istimewa ini, berdoa agar Tuhan Yesus selalu melindungi dan memberkati langkah-langkahmu kedepan.\n"
        "Semoga tahun ini menjadi tahun yang penuh dengan kemurahan Tuhan dalam hidupmu.\n\n"
        "Salam kasih,\n IT & Media GPdI Pembaharuan"
    )

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = email_penerima

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
        logger.info("Email berhasil dikirim ke %s", email_penerima)
        return True
    except Exception as e:
        st.warning(f"Gagal kirim email ke {email_penerima}: {e}")
        logger.warning("Gagal kirim email ke %s: %s", email_penerima, e)
        return False
