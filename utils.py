from datetime import date, datetime
import smtplib
from email.message import EmailMessage
import streamlit as st

def load_data_jemaat():
    return st.session_state.get("data_jemaat", [])

def parse_tanggal_lahir(tgl_str):
    try:
        return datetime.strptime(tgl_str, "%d-%m-%y").date()
    except Exception as e:
        st.warning(f"Gagal parsing tanggal: {tgl_str} | Error: {e}")
        return None

def filter_ulang_tahun_hari_ini():
    today = date.today()
    jemaat = load_data_jemaat()
    hasil = []

    for j in jemaat:
        tgl_lahir_raw = j.get("Tgl Lahir", "")
        parsed = parse_tanggal_lahir(tgl_lahir_raw)
        if parsed and parsed.day == today.day and parsed.month == today.month:
            hasil.append(j)
    return hasil

def kirim_email_ultah(nama, email_penerima):
    sender = st.secrets["email_smtp"]["sender"]
    password = st.secrets["email_smtp"]["app_password"]

    subject = "🎉 Selamat Ulang Tahun!"
    body = (
        f"Syalom {nama},\n\n"
        "Selamat ulang tahun! Kiranya Tuhan Yesus memberkati umur dan perjalanan hidupmu ke depan.\n\n"
        "Salam kasih,\nTim IT GPdI Pembaharuan"
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
        return True
    except Exception as e:
        st.warning(f"Gagal kirim email ke {email_penerima}: {e}")
        return False
