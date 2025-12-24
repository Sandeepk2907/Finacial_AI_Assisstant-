from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from utils.ai_engine import get_answer
from utils.tts import speak
from utils.stt import listen
from deep_translator import GoogleTranslator
import os, time, uuid, sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


APP_ROOT = os.path.dirname(__file__)
DB_PATH = os.path.join(APP_ROOT, "users.db")
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "replace_with_a_real_secret_key")
REQUIRE_LOGIN = True  
# ----------------------
# App init
# ----------------------
app = Flask(__name__)
app.secret_key = SECRET_KEY

# ensure audio folder exists
os.makedirs(os.path.join(app.root_path, "static", "audio"), exist_ok=True)

# ----------------------
# Database helpers
# ----------------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH,  timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# create DB/table at startup
init_db()

# ----------------------
# Auth routes
# ----------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not username or not password:
            flash("Please enter username and password.", "danger")
            return redirect(url_for("signup"))
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("signup"))

        password_hash = generate_password_hash(password)
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                        (username, email, password_hash))
            conn.commit()
            conn.close()
            flash("Account created successfully. Please login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username or email already exists. Choose another.", "danger")
            return redirect(url_for("signup"))
        except Exception as e:
            flash("Error creating account: " + str(e), "danger")
            return redirect(url_for("signup"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Logged in successfully.", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

# ----------------------
# Chat / TTS helpers (kept your logic)
# ----------------------
def generate_tts_audio(response_text, lang):
    """Generate a unique MP3 file and return its /static/ path."""
    try:
        audio_dir = os.path.join(app.root_path, "static", "audio")
        os.makedirs(audio_dir, exist_ok=True)

        filename = f"response_{int(time.time())}_{uuid.uuid4().hex[:6]}.mp3"
        audio_path = os.path.join(audio_dir, filename)

        print(f"🎧 Generating TTS in language: {lang}")
        # speak signature expected: speak(text, lang_code=..., output_path=...)
        # (your tts.py should match this signature)
        success = speak(response_text, lang_code=lang, output_path=audio_path)

        # small sleep to ensure file is flushed to disk
        time.sleep(0.4)

        if not success or not os.path.exists(audio_path):
            print("❌ TTS failed or file not found.")
            return None

        print(f"✅ Audio file ready at {audio_path}")
        return f"/static/audio/{filename}"

    except Exception as e:
        print("TTS generation error:", e)
        return None

# ----------------------
# Protected index (chat)
# ----------------------
@app.route("/")
def index():
    if REQUIRE_LOGIN and not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("index.html")

# ----------------------
# Ask & Speak endpoints (unchanged behaviour, integrated with translator)
# ----------------------
@app.route("/ask", methods=["POST"])
def ask():
    query = request.form.get("query", "")
    language = request.form.get("language", "en")

    if not query:
        return jsonify({"response": "Please enter a question.", "audio": None})

    try:
        # Step 1: Get English response (AI logic lives in utils.ai_engine.get_answer)
        response_text = get_answer(query)

        # Step 2: Translate to selected language (if required)
        translated_text = (
            GoogleTranslator(source="auto", target=language).translate(response_text)
            if language != "en"
            else response_text
        )

        # Step 3: Generate TTS in the same language
        audio_url = generate_tts_audio(translated_text, language)

        return jsonify({"response": translated_text, "audio": audio_url})

    except Exception as e:
        print("Error in /ask:", e)
        return jsonify({"response": f"Error: {e}", "audio": None})

@app.route("/speak", methods=["GET"])
def speak_to_text():
    try:
        language = request.args.get("language", "en")
        print(f"🎙️ Listening for {language} input...")

        # Step 1: Capture voice
        query = listen()

        if not query or "Error" in query:
            return jsonify({
                "query": query,
                "response": "Sorry, I couldn’t understand your speech.",
                "audio": None
            })

        print(f"🗣️ You said ({language}): {query}")

        # Step 2: Translate voice query to English for AI processing (if user used hi/kn)
        if language != "en":
            translated_query = GoogleTranslator(source="auto", target="en").translate(query)
            print(f"🌐 Translated to English: {translated_query}")
        else:
            translated_query = query

        # Step 3: Get AI answer in English
        response_text = get_answer(translated_query)

        # Step 4: Translate AI response back to user's selected language
        if language != "en":
            translated_response = GoogleTranslator(source="auto", target=language).translate(response_text)
        else:
            translated_response = response_text

        # Step 5: Generate speech in selected language
        audio_data_url = generate_tts_audio(translated_response, language)

        print(f"✅ Responding in {language}")
        return jsonify({
            "query": query,
            "response": translated_response,
            "audio": audio_data_url
        })

    except Exception as e:
        print("🎤 Voice processing error:", e)
        return jsonify({
            "query": None,
            "response": f"Error: {e}",
            "audio": None
        })

# ----------------------
# Run
# ----------------------
if __name__ == "__main__":
    os.makedirs(os.path.join(app.root_path, "static", "audio"), exist_ok=True)
    app.run(debug=True)
