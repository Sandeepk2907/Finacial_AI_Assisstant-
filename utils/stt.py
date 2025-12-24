import speech_recognition as sr

def listen(language: str = "en", timeout: int = 6, phrase_time_limit: int = 6):
    """
    Captures audio from the user's microphone and converts it to text using Google's STT.
    Returns recognized text, or an error message string if failed.
    """
    recognizer = sr.Recognizer()

    # Ensure all thresholds are numeric (to avoid '>' between float and str error)
    recognizer.energy_threshold = 300
    recognizer.pause_threshold = 0.8
    recognizer.dynamic_energy_threshold = True

    try:
        with sr.Microphone() as source:
            print(f"🎙️ Listening for {language} input...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("🎤 Listening... Speak now!")

            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        # Map UI language code to Google's STT language codes
        lang_map = {
            "en": "en-IN",   # English (India)
            "hi": "hi-IN",   # Hindi
            "kn": "kn-IN"    # Kannada
        }
        lang_code = lang_map.get(language, "en-IN")

        # Perform recognition
        text = recognizer.recognize_google(audio, language=lang_code)
        print(f"🗣️ You said: {text}")
        return text

    except sr.UnknownValueError:
        print("❌ Could not understand the audio.")
        return "Error: Could not capture speech."
    except sr.RequestError as e:
        print(f"⚠️ Could not request results from Google STT service: {e}")
        return "Error: Speech recognition request failed."
    except sr.WaitTimeoutError:
        print("⌛ Listening timed out.")
        return "Error: Listening timed out."
    except Exception as e:
        print(f"Microphone error: {e}")
        return "Error: Microphone access failed."
