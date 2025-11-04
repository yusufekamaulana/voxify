import os, json, datetime, io
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename
import soundfile as sf

# ====================================================
# FLASK CONFIGURATION
# ====================================================
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("VOXIFY_SECRET_KEY", "dev_secret_key")  # safe fallback

# ====================================================
# KONFIGURASI FFmpeg untuk Pydub
# ====================================================
FFMPEG_BIN = "ffmpeg-8.0-essentials_build/ffmpeg-8.0-essentials_build/bin/"
os.environ["PATH"] += os.pathsep + FFMPEG_BIN

from pydub import AudioSegment
from pydub.utils import which

AudioSegment.converter = which("ffmpeg") or os.path.join(FFMPEG_BIN, "ffmpeg.exe")
AudioSegment.ffprobe   = which("ffprobe") or os.path.join(FFMPEG_BIN, "ffprobe.exe")

# ====================================================
# IMPORT FUNGSI MODEL
# ====================================================
from utils.inference import prediksi_audio

# ====================================================
# KONFIGURASI FLASK
# ====================================================

USERS_FILE = "users.json"
HISTORY_FILE = "history.json"
UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXT = {"wav", "mp3", "ogg", "m4a", "webm"}

# ====================================================
# HELPER FUNCTIONS
# ====================================================
def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    with open(HISTORY_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def add_history(username, filename, duration, label_pred):
    history = load_history()
    user_history = history.get(username, [])
    user_history.append({
        "filename": filename,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "duration": duration,
        "label_pred": label_pred
    })
    history[username] = user_history
    save_history(history)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

# ====================================================
# PAGE ROUTES
# ====================================================
@app.route("/")
def index():
    return render_template("login.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/home")
def home():
    username = session.get("username", "Guest")
    return render_template("home.html", username=username)

@app.route("/onboarding")
def onboarding():
    return render_template("onboarding.html")

@app.route("/measuring")
def measuring():
    return render_template("measuring.html")

@app.route("/report")
def report():
    hasil_pred = session.get("hasil_pred")
    filename = session.get("last_audio")
    label_pred = session.get("label_pred")
    duration = session.get("duration")
    waktu = datetime.datetime.now().strftime("%d %B %Y, %H:%M WIB")

    if not hasil_pred:
        return redirect(url_for("measuring"))

    return render_template(
        "report.html",
        filename=filename,
        waktu=waktu,
        hasil_pred=hasil_pred,
        label_pred=label_pred,
        duration=duration
    )

# ====================================================
# INFERENCE ROUTE
# ====================================================
@app.route("/predict", methods=["POST"])
def predict():
    if "audio_file" not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    file = request.files["audio_file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    input_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
    file.save(input_path)
    print(f"[INFO] File uploaded: {input_path}")

    temp_wav = os.path.join(UPLOAD_FOLDER, "converted.wav")
    duration_sec = None
    try:
        audio = AudioSegment.from_file(input_path)
        duration_sec = round(len(audio) / 1000.0, 2)
        print(f"[INFO] Detected duration: {duration_sec} seconds")
        audio.export(temp_wav, format="wav")
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": f"Gagal konversi audio: {str(e)}"}), 500

    try:
        print("[INFO] Starting model prediction...")
        label, hasil_pred = prediksi_audio(temp_wav)
        print(f"[INFO] Prediction success → {label}")

        session["hasil_pred"] = hasil_pred
        session["last_audio"] = file.filename
        session["label_pred"] = label
        session["duration"] = float(duration_sec or 0.0)

        username = session.get("username", "guest")
        add_history(username, file.filename, duration_sec, label)

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": f"Gagal prediksi: {str(e)}"}), 500

    try:
        os.remove(input_path)
        os.remove(temp_wav)
    except Exception:
        pass

    print(f"[INFO] Redirecting to /report (duration={duration_sec}s)...")
    return redirect(url_for("report"))

# ====================================================
# API: LOGIN / SIGNUP / LOGOUT / HISTORY
# ====================================================
@app.route("/api/signup", methods=["POST"])
def api_signup():
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"status": "error", "message": "All fields are required"}), 400

    users = load_users()
    if any(u["username"] == username or u["email"] == email for u in users):
        return jsonify({"status": "error", "message": "User already exists"}), 400

    users.append({"username": username, "email": email, "password": password})
    save_users(users)
    return jsonify({"status": "success", "message": "Account created successfully!"})

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    users = load_users()
    found = next(
        (u for u in users if (u["username"] == username or u["email"] == username)
         and u["password"] == password),
        None
    )

    if found:
        session["username"] = found["username"]
        return jsonify({"status": "success", "message": "Login successful!"})
    else:
        return jsonify({"status": "error", "message": "Invalid username or password"}), 401

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"status": "success", "message": "Logged out"})

@app.route("/history")
def history():
    username = session.get("username")
    if not username:
        return jsonify({"error": "User not logged in"}), 401
    history = load_history().get(username, [])
    return jsonify(history)

from utils.filter_model import predict_filter
@app.route("/filter", methods=["POST"])
def filter_sound():
    if "audio_file" not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    file = request.files["audio_file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    input_path = os.path.join(UPLOAD_FOLDER, secure_filename(file.filename))
    file.save(input_path)

    temp_wav = os.path.join(UPLOAD_FOLDER, "converted.wav")
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(temp_wav, format="wav")
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": f"Gagal konversi audio: {str(e)}"}), 500

    # =====================================================
    # Tahap: Jalankan Filter Noise
    # =====================================================
    try:
        filter_result = predict_filter(temp_wav)
        print(f"[FILTER] {filter_result['hasil']}")

        # Jika bukan suara napas, langsung kembalikan respons
        if filter_result["label"] == "Non-Respiratory":
            return jsonify({
                "status": "rejected",
                "message": filter_result["hasil"],
                "prob": filter_result["prob"]
            }), 200

        # Jika valid → lanjutkan ke halaman measuring atau prediksi
        session["filter_result"] = filter_result
        return jsonify({
            "status": "accepted",
            "message": filter_result["hasil"],
            "prob": filter_result["prob"]
        }), 200

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": f"Gagal menjalankan filter: {str(e)}"}), 500

    finally:
        try:
            os.remove(input_path)
            os.remove(temp_wav)
        except Exception:
            pass


# ====================================================
# MAIN ENTRY
# ====================================================
if __name__ == "__main__":
    app.run(debug=True)
