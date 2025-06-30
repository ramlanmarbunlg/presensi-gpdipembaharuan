import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
from pyzbar.pyzbar import decode
import numpy as np
from PIL import Image
import av  # Digunakan oleh streamlit-webrtc untuk menangani frame video

# Set judul halaman dan ikon browser
st.set_page_config(page_title="Scan QR", page_icon="📷")
st.title("📷 Scan QR Code Kehadiran")

# ========================
# 👇 Kelas pemrosesan video dari webcam
# ========================
class QRScanner(VideoTransformerBase):
    def __init__(self):
        self.qr_data = None  # Menyimpan hasil QR yang berhasil terbaca

    # Fungsi ini dipanggil untuk setiap frame video
    def transform(self, frame):
        # Konversi frame dari format AV ke NumPy array (OpenCV-style)
        img = frame.to_ndarray(format="bgr24")
        
        # Konversi ke PIL image karena pyzbar butuh format ini
        pil_img = Image.fromarray(img)

        # Deteksi QR Code
        barcodes = decode(pil_img)
        for barcode in barcodes:
            # Ambil data dari QR yang ditemukan
            self.qr_data = barcode.data.decode("utf-8")

        return img  # Tampilkan kembali frame video tanpa perubahan visual

# ========================
# 👇 Aktifkan webcam dengan streamlit-webrtc
# ========================
ctx = webrtc_streamer(
    key="qr-scan",  # Unik per pemanggilan
    video_processor_factory=QRScanner,  # Gunakan kelas di atas untuk proses frame
    media_stream_constraints={"video": True, "audio": False},  # Hanya kamera, tanpa mic
    async_processing=True,  # Izinkan pemrosesan asynchronous
)

# ========================
# 👇 Jika QR berhasil dibaca
# ========================
if ctx.video_processor:
    result = ctx.video_processor.qr_data
    if result:
        # Tampilkan QR yang berhasil dibaca
        st.success(f"✅ QR Code Terbaca: **{result}**")

        # Simpan ke session_state agar bisa dipakai di halaman lain
        st.session_state["qr_ditemukan"] = result
