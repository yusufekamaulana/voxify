import numpy as np, tensorflow as tf
import tensorflow as tf
from tensorflow import keras

# from utils.feature_extractor import muat_dan_resample, ekstrak_fitur
from utils.features_extractor import muat_dan_resample, ekstrak_fitur


MODEL_PATH = "model/CNN_Fusion_2D.h5"  # ubah path sesuai kondisi
model = tf.keras.models.load_model(MODEL_PATH)

LABELS = ['Bronchiectasis', 'Bronchiolitis', 'COPD', 'Healthy', 'Pneumonia', 'URTI']

def pad_and_expand(X, time_target=2579):
    C, T = X.shape
    T_new = min(time_target, T)
    out = np.zeros((C, time_target), dtype=np.float32)
    out[:, :T_new] = X[:, :T_new]
    return out[..., np.newaxis][np.newaxis, ...]


def prediksi_audio(path_audio):
    y, sr = muat_dan_resample(path_audio)
    mel, mfcc, spec = ekstrak_fitur(y, sr)
    mel_in  = pad_and_expand(mel)
    mfcc_in = pad_and_expand(mfcc)
    spec_in = pad_and_expand(spec)

    yprob = model.predict([mel_in, mfcc_in, spec_in], verbose=0)[0]

    # ✅ ubah dari np.float32 → float bawaan Python agar bisa di-JSONify
    hasil = {label: float(prob.round(4)) for label, prob in zip(LABELS, yprob)}
    pred_label = LABELS[np.argmax(yprob)]

    return pred_label, hasil
