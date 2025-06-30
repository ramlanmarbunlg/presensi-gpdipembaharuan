import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import cv2
import numpy as np
import av

# Set judul halaman dan icon
st.set_page_config(page_title="Scan QR", page_icon="📷")
st.title("📷 Scan QR Code Kehadiran")

# ========================
# QR Scanner tanpa zbar (pakai OpenCV)
# ========================
class QRScannerCV(VideoTransformerBase):
    def __init__(self):
        self.qr_data = None
        self.detector = cv2.QRCodeDetector()

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        data, bbox, _ = self.detector.detectAndDecode(img)
        if data:
            self.qr_data = data
        return img

# ========================
# Streaming Webcam
# ========================
ctx = webrtc_streamer(
    key="scan-qr",
    video_processor_factory=QRScannerCV,
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True,
)

# ========================
# QR Berhasil dibaca
# ========================
if ctx.video_processor:
    result = ctx.video_processor.qr_data
    if result:
        st.success(f"✅ QR Code Terbaca: **{result}**")
        st.session_state["qr_ditemukan"] = result
