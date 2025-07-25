from datetime import date
import smtplib
from email.message import EmailMessage
import streamlit as st

def load_data_jemaat():
    # Fungsi ini memuat database jemaat Anda
    # Sesuaikan ini dengan sumber datanya
    return st.session_state.get("data_jemaat", [])

def filter_ulang_tahun_hari_ini():
    today = date.today()
    jemaat = load_data_jemaat()
    return [
        j for j in jemaat
        if "Tanggal_Lahir" in j and j["Tgl Lahir"]
        and datetime.strptime(j["Tanggal_Lahir"], "%d-%m-%Y").month == today.month
        and datetime.strptime(j["Tanggal_Lahir"], "%d-%m-%Y").day == today.day
    ]

def kirim_email_ultah(nama, email_penerima):
    sender = st.secrets["email_smtp"]["sender"]
    password = st.secrets["email_smtp"]["app_password"]

    subject = "🎉 Selamat Ulang Tahun!"
    body = f"Halo {nama},\n\nSelamat ulang tahun! Tuhan memberkati dan menyertai selalu.\n\nSalam,\nGereja GPdI Pembaharuan"

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = email_penerima

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)
