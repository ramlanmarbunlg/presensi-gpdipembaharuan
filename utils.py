from datetime import date, datetime
import smtplib
from email.message import EmailMessage
import streamlit as st

def load_data_jemaat():
    # Load dari session state atau ganti sesuai database aslinya
    return st.session_state.get("data_jemaat", [])

def filter_ulang_tahun_hari_ini():
    today = date.today()
    jemaat = load_data_jemaat()
    
    hasil = []
    for j in jemaat:
        tgl_lahir_str = j.get("Tgl Lahir", "").strip()
        if tgl_lahir_str:
            try:
                tgl_lahir = datetime.strptime(tgl_lahir_str, "%d-%m-%Y")
                if tgl_lahir.day == today.day and tgl_lahir.month == today.month:
                    hasil.append(j)
            except ValueError:
                pass  # Abaikan jika format salah
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
