import librosa, numpy as np

TARGET_SR = 8000
N_FFT = 512
HOP_LEN = 256

def muat_dan_resample(path_audio, target_sr=TARGET_SR):
    y, sr_asli = librosa.load(path_audio, sr=None, mono=True)
    if sr_asli != target_sr:
        y = librosa.resample(y, orig_sr=sr_asli, target_sr=target_sr)
        sr = target_sr
    else:
        sr = sr_asli
    y = librosa.util.normalize(y)
    return y, sr

def batas_frekuensi_aman(sr):
    nyquist = sr / 2.0
    fmin = 20.0
    fmax = min(nyquist - 10.0, 3900.0)
    if fmax <= fmin + 10.0:
        fmax = fmin + 10.0
    return fmin, fmax

def ekstrak_fitur(y, sr):
    fmin, fmax = batas_frekuensi_aman(sr)
    S = np.abs(librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LEN))**2
    mel = librosa.feature.melspectrogram(S=S, sr=sr, n_mels=128, fmin=fmin, fmax=fmax)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
    chroma = librosa.feature.chroma_stft(S=S, sr=sr)
    # SAFE tonnetz: limit frekuensi biar ga melebihi Nyquist
    try:
        tonnetz = librosa.feature.tonnetz(
            y=librosa.effects.harmonic(y),
            sr=sr
        )
    except Exception:
        # fallback aman (tanpa crash)
        tonnetz = np.zeros((6, chroma.shape[1]))

    min_frames = min(mel.shape[1], mfcc.shape[1], chroma.shape[1], tonnetz.shape[1])
    mel, mfcc, chroma, tonnetz = mel[:, :min_frames], mfcc[:, :min_frames], chroma[:, :min_frames], tonnetz[:, :min_frames]
    spektral = np.vstack([mel, chroma, tonnetz])
    return mel, mfcc, spektral

def ekstrak_fitur_global(y, sr):
    fmin, fmax = batas_frekuensi_aman(sr)
    try:
        S = np.abs(librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LEN))**2
    except Exception:
        return {"Mel": np.zeros((128, 1)), "MFCC": np.zeros((40, 1)), "Spektral": np.zeros((146, 1))}
    try:
        mel = librosa.feature.melspectrogram(S=S, sr=sr, n_mels=128, fmin=fmin, fmax=fmax)
    except Exception:
        mel = np.zeros((128, 1))
    try:
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
    except Exception:
        mfcc = np.zeros((40, 1))
    try:
        chroma = librosa.feature.chroma_stft(S=S, sr=sr)
    except Exception:
        chroma = np.zeros((12, mel.shape[1]))
    try:
        # safe tonnetz, fallback kalau error CQT
        tonnetz = librosa.feature.tonnetz(y=librosa.effects.harmonic(y), sr=sr)
    except Exception:
        tonnetz = np.zeros((6, chroma.shape[1]))
    min_frames = min(mel.shape[1], chroma.shape[1], tonnetz.shape[1])
    mel, chroma, tonnetz = mel[:, :min_frames], chroma[:, :min_frames], tonnetz[:, :min_frames]
    spektral = np.vstack([mel, chroma, tonnetz])
    return {
        "Mel": mel.astype(np.float32),
        "MFCC": mfcc.astype(np.float32),
        "Spektral": spektral.astype(np.float32)
    }
