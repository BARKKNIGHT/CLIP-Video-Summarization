from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    send_from_directory,
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import cv2
import secrets
from datetime import datetime, timedelta, timezone
from models import db, User, Video
from config import Config
import logging
from functools import wraps
import requests
import openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Create required directories
for folder in [app.config["UPLOAD_FOLDER"], app.config["THUMBNAIL_FOLDER"]]:
    os.makedirs(folder, exist_ok=True)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"
mail = Mail(app)

# OpenAI API key
openai.api_key = Config.OPENAI_API_KEY


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def generate_token(length=32):
    return secrets.token_hex(length // 2)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    )


def send_email(subject, recipient, html_content):
    try:
        msg = Message(
            subject,
            sender=Config.MAIL_USERNAME,
            recipients=[recipient],
            html=html_content,
        )
        mail.send(msg)
        return True
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False


def get_transcription(file_path):
    url = "http://localhost:5001/transcribe"
    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(url, files=files, timeout=300)
        response.raise_for_status()
        data = response.json()
        return data.get("transcription", "")
    except Exception as e:
        logger.error(f"Whisper API error: {str(e)}")
        return ""


def extract_keyframes(video_path, num_frames=15):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_ids = [
        int(total_frames / num_frames * i) for i in range(num_frames)
    ]
    keyframe_paths = []

    for idx, frame_id in enumerate(frame_ids):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ret, frame = cap.read()
        if ret:
            frame_path = f"/tmp/keyframe_{secrets.token_hex(4)}_{idx}.jpg"
            cv2.imwrite(frame_path, frame)
            keyframe_paths.append(frame_path)
    cap.release()
    return keyframe_paths


def get_frame_descriptions(frame_paths):
    url = "http://localhost:5002/describe"
    files = [
        ("images", (os.path.basename(path), open(path, "rb"), "image/jpeg"))
        for path in frame_paths
    ]
    try:
        response = requests.post(url, files=files, timeout=300)
        response.raise_for_status()
        return response.json().get("descriptions", [])
    except Exception as e:
        logger.error(f"SmolVLM API error: {str(e)}")
        return []


def summarize_video(descriptions, transcription):
    prompt = "Video keyframe descriptions:\n"
    for idx, desc in enumerate(descriptions, 1):
        prompt += f"Frame {idx}: {desc}\n"
    if transcription:
        prompt += f"\nTranscription:\n{transcription}\n"
    prompt += "\nProvide a concise summary of the video content."

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=300,
            temperature=0.5,
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return ""


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        remember = request.form.get("remember", False)

        if not email or not password:
            flash("Please fill in all fields.", "error")
            return render_template("login.html")

        user = User.query.filter_by(email=email.lower()).first()
        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email", "").lower()
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not all([username, email, password, confirm_password]):
            flash("Please fill in all fields.", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return render_template("register.html")

        try:
            user = User(
                username=username,
                email=email,
                password=generate_password_hash(password),
                created_at=datetime.now(timezone.utc),
            )
            db.session.add(user)
            db.session.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}")
            db.session.rollback()
            flash("An error occurred during registration.", "error")

    return render_template("register.html")


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form.get("email", "").lower()
        if not email:
            flash("Please enter your email address.", "error")
            return render_template("reset_password.html")

        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_token()
            user.reset_token = token
            user.reset_token_expiry = datetime.now(timezone.utc) + timedelta(hours=24)
            db.session.commit()

            reset_link = url_for("reset_password_confirm", token=token, _external=True)
            html_content = render_template(
                "email/reset_password.html", user=user, reset_link=reset_link
            )

            if send_email("Password Reset Request", user.email, html_content):
                flash(
                    "Password reset instructions have been sent to your email.",
                    "success",
                )
            else:
                flash("Error sending reset email. Please try again later.", "error")
        else:
            flash(
                "If an account exists with this email, you will receive reset instructions.",
                "info",
            )

    return render_template("reset_password.html")


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password_confirm(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user or (
        user.reset_token_expiry
        and user.reset_token_expiry < datetime.now(timezone.utc)
    ):
        flash("Invalid or expired reset token.", "error")
        return redirect(url_for("reset_password"))

    if request.method == "POST":
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not password or not confirm_password:
            flash("Please fill in all fields.", "error")
            return render_template("reset_password_confirm.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("reset_password_confirm.html")

        user.password = generate_password_hash(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()

        flash("Your password has been reset successfully.", "success")
        return redirect(url_for("login"))

    return render_template("reset_password_confirm.html")

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        if "video" not in request.files:
            flash("No file part", "error")
            return redirect(request.url)

        file = request.files["video"]
        if file.filename == "":
            flash("No selected file", "error")
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash("Invalid file type", "error")
            return redirect(request.url)

        try:
            filename = secure_filename(file.filename)
            base_name, extension = os.path.splitext(filename)
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"{base_name}_{timestamp}{extension}"
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

            file.save(file_path)

            # Generate thumbnail (first frame)
            video_cap = cv2.VideoCapture(file_path)
            ret, frame = video_cap.read()
            if ret:
                thumbnail_filename = f"thumb_{timestamp}.jpg"
                thumbnail_path = os.path.join(
                    app.config["THUMBNAIL_FOLDER"], thumbnail_filename
                )
                cv2.imwrite(thumbnail_path, frame)
                video_cap.release()
            else:
                video_cap.release()
                os.remove(file_path)
                flash("Error generating thumbnail", "error")
                return redirect(request.url)

            # Transcribe audio using Whisper microservice
            transcription = get_transcription(file_path)

            # Extract keyframes
            keyframe_paths = extract_keyframes(file_path, num_frames=15)

            # Get descriptions from SmolVLM microservice
            descriptions = get_frame_descriptions(keyframe_paths)

            # Clean up keyframe temp files
            for path in keyframe_paths:
                try:
                    os.remove(path)
                except Exception:
                    pass

            # Summarize video with OpenAI
            summary = summarize_video(descriptions, transcription)

            # Save video entry
            video_entry = Video(
                filename=filename,
                thumbnail_path=thumbnail_filename,
                user_id=current_user.id,
                upload_date=datetime.now(timezone.utc),
                transcription=transcription,
                summary=summary,
            )
            db.session.add(video_entry)
            db.session.commit()

            flash("Video uploaded and processed successfully!", "success")

        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            flash("Error uploading file", "error")
            return redirect(request.url)

        return redirect(url_for("dashboard"))

    return render_template("upload.html")


@app.route("/dashboard")
@login_required
def dashboard():
    page = request.args.get("page", 1, type=int)
    videos = Video.query.filter_by(user_id=current_user.id).paginate(
        page=page, per_page=12
    )
    return render_template("dashboard.html", videos=videos)


@app.route("/video/<int:video_id>")
@login_required
def video_detail(video_id):
    video = Video.query.get_or_404(video_id)
    if video.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    return render_template("video_detail.html", video=video)

@app.route("/video/<int:video_id>/delete", methods=["POST"])
@login_required
def delete_video(video_id):
    video = Video.query.get_or_404(video_id)
    if video.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    try:
        # Delete files
        video_path = os.path.join(app.config["UPLOAD_FOLDER"], video.filename)
        thumbnail_path = os.path.join(
            app.config["THUMBNAIL_FOLDER"], video.thumbnail_path
        )

        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)

        db.session.delete(video)
        db.session.commit()
        flash("Video deleted successfully.", "success")
    except Exception as e:
        logger.error(f"Error deleting video: {str(e)}")
        flash("Error deleting video.", "error")

    return redirect(url_for("dashboard"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("login"))


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("errors/500.html"), 500

# ... (rest of your routes: login, register, reset password, delete video, etc.)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=3000)

