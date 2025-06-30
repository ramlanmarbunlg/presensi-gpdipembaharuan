import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
from pyzbar.pyzbar import decode
import numpy as np
from PIL import Image
import av

st.set_page_config(page_title="Scan QR", page_icon="📷")
st.title("📷 Scan QR Code Kehadiran")

class QRScanner(VideoTransformerBase):
    def __init__(self):
        self.qr_data = None

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        pil_img = Image.fromarray(img)
        barcodes = decode(pil_img)
        for barcode in barcodes:
            self.qr_data = barcode.data.decode("utf-8")
        return img

ctx = webrtc_streamer(
    key="qr-scan",
    video_processor_factory=QRScanner,
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True,
)

if ctx.video_processor:
    result = ctx.video_processor.qr_data
    if result:
        st.success(f"✅ QR Code Terbaca: **{result}**")
        st.session_state["qr_ditemukan"] = result
