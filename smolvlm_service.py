# smolvlm_service.py
from flask import Flask, request, jsonify
from transformers import AutoProcessor, AutoModelForVision2Seq
from PIL import Image
import tempfile
import os

app = Flask(__name__)

# Load SmolVLM model once
processor = AutoProcessor.from_pretrained("HuggingFaceTB/SmolVLM-Instruct")
model = AutoModelForVision2Seq.from_pretrained("HuggingFaceTB/SmolVLM-Instruct")

@app.route("/describe", methods=["POST"])
def describe():
    descriptions = []
    files = request.files.getlist("images")
    if not files:
        return jsonify({"error": "No images uploaded"}), 400

    for file in files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            file.save(tmp.name)
            try:
                image = Image.open(tmp.name).convert("RGB")
                prompt = "Describe this image?"
                inputs = processor(prompt, image, return_tensors="pt").to(model.device)
                generated_ids = model.generate(**inputs, max_new_tokens=50)
                description = processor.batch_decode(
                    generated_ids, skip_special_tokens=True
                )[0].strip()
                descriptions.append(description)
            except Exception as e:
                descriptions.append(f"Error: {str(e)}")
            finally:
                os.remove(tmp.name)

    return jsonify({"descriptions": descriptions})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
