from gtts import gTTS
import os, time

def speak(text, lang_code='en', output_path=None):

    try:
        if not output_path:
            raise ValueError("output_path must be provided")

        # Ensure output folder exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Map supported language codes (for safety)
        lang_map = {"en": "en", "hi": "hi", "kn": "kn"}
        lang = lang_map.get(lang_code, "en")

        print(f"🔊 Generating TTS for '{lang}' language...")

        # Create TTS and save
        tts = gTTS(text=text, lang=lang)
        tts.save(output_path)

        # Give a short pause for Windows file handling
        time.sleep(0.3)

        # Confirm file exists
        if os.path.exists(output_path):
            print(f"✅ TTS file created at: {output_path}")
            return True
        else:
            print(f"⚠️ File not found after saving: {output_path}")
            return False

    except Exception as e:
        print(f"❌ TTS Error: {e}")
        return False
