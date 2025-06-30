import streamlit as st
import cv2
from pyzbar.pyzbar import decode
from PIL import Image
import datetime

st.set_page_config(page_title="Scan QR Absensi Jemaat", page_icon="📷")

st.title("📷 Scan QR Code Kehadiran Jemaat")

# Webcam aktif
run = st.checkbox("✅ Aktifkan Kamera")

FRAME_WINDOW = st.image([])

cap = None
if run:
    cap = cv2.VideoCapture(0)

while run and cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Deteksi QR
    for barcode in decode(frame):
        qr_data = barcode.data.decode('utf-8')
        pts = barcode.polygon
        (x, y, w, h) = barcode.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 255), 2)
        cv2.putText(frame, f"ID: {qr_data}", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

        st.success(f"✅ QR Terdeteksi: **{qr_data}**")
        st.session_state['qr_ditemukan'] = qr_data
        st.session_state['waktu_scan'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        run = False
        cap.release()
        break

    # Tampilkan gambar webcam
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    FRAME_WINDOW.image(frame)

# Hasil akhir setelah deteksi
if 'qr_ditemukan' in st.session_state:
    st.info(f"🆔 ID Jemaat: **{st.session_state['qr_ditemukan']}**")
    st.write(f"🕒 Waktu Absen: `{st.session_state['waktu_scan']}`")

    if st.button("📤 Simpan ke Google Sheets"):
        st.success("🚀 Data siap disimpan (fungsi Google Sheets di langkah berikutnya).")
