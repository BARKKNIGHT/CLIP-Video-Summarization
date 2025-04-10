# whisper_service.py
from flask import Flask, request, jsonify
import whisper
import tempfile
import os

app = Flask(__name__)

# Load Whisper model once at startup
model = whisper.load_model("base")  # or "small", "medium", "large"

@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        file.save(tmp.name)
        try:
            result = model.transcribe(tmp.name)
            return jsonify({"transcription": result["text"]})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            os.remove(tmp.name)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
