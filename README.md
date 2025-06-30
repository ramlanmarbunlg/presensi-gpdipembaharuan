# Aplikasi Presensi GPdI Pembaharuan

A simple Streamlit app template for you to modify!

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://blank-app-template.streamlit.app/)

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```

**Notes:**
- ❌ Streamlit Cloud tidak mendukung OpenCV berbasis native bindings seperti cv2 secara penuh
- ✅ Modul cv2 memerlukan pustaka native C/C++ (misalnya .so, .dll, atau .dylib) yang tidak bisa dibuild atau dijalankan di lingkungan terbatas seperti Streamlit Cloud.
- ✅ Solusi Alternatif Scan QR Tanpa OpenCV, saya menggunakan streamlit-webrtc + pyzbar yang memang didukung Streamlit Cloud.
- ✅ Kelebihan streamlit-webrtc + pyzbar:
  - Tidak perlu cv2
  - Aman digunakan di Streamlit Cloud
  - Tetap real-time dari webcam
  - Bisa langsung dikembangkan untuk absensi + simpan ke Google Sheets
