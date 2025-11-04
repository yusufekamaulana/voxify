import os
import joblib
import numpy as np
import librosa

# ============================================
# LOAD MODEL SAAT SERVER DIMULAI
# ============================================
MODEL_PATH = os.path.join("model", "respiratory_detector_lgbm.pkl")

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model filter tidak ditemukan di {MODEL_PATH}")

model = joblib.load(MODEL_PATH)
print(f"[INFO] Filter model berhasil dimuat dari {MODEL_PATH}")

# ============================================
# EKSTRAKSI FITUR AUDIO
# ============================================
def extract_features(path, sr=16000, n_mfcc=20):
    """
    Mengubah audio menjadi fitur numerik berbasis MFCC (mean + std).
    Digunakan sebagai input untuk model filter noise.
    """
    y, _ = librosa.load(path, sr=sr)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    feat = np.concatenate([mfcc.mean(axis=1), mfcc.std(axis=1)])
    return feat.reshape(1, -1)

# ============================================
# FUNGSI FILTER
# ============================================
def filter_audio(file_path):
    """
    Melakukan prediksi apakah audio adalah suara napas (respiratory)
    atau non-napas (noise, ucapan, musik, dll.)
    """
    feat = extract_features(file_path)
    pred = model.predict(feat)[0]
    prob = model.predict_proba(feat)[0][1]

    if pred == 1:
        label = "Respiratory"
        result = ""
    else:
        label = "Non-Respiratory"
        result = ""

    return label, result, float(prob)

# ============================================
# WRAPPER UNTUK FLASK ROUTE
# ============================================
def predict_filter(temp_wav_path):
    """
    Fungsi utama yang dipanggil Flask.
    Mengembalikan dict hasil filter agar mudah digunakan di route /filter.
    """
    label, result, prob = filter_audio(temp_wav_path)
    return {
        "label": label,
        "hasil": result,
        "prob": prob
    }
