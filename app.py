from flask import Flask, request, jsonify, render_template, session as flask_session, redirect, url_for, flash
from flask.logging import create_logger
import logging
from pymongo.mongo_client import MongoClient
from pymongo import errors
from gridfs import GridFS
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import timedelta
import cv2
import numpy as np
import dotenv
import datetime
import onnxruntime as ort

dotenv.load_dotenv()

# Initialize Flask App
app = Flask(__name__)
LOG = create_logger(app)
LOG.setLevel(logging.INFO)

# App Configuration
app.secret_key = os.getenv("SECRET_KEY")
app.permanent_session_lifetime = timedelta(days=1)

# MongoDB Configuration
uri = os.getenv("MONGODB_URI")
client = MongoClient(uri)
db = client['malaria_detection_db']
fs = GridFS(db)
users_collection = db['users']  # Collection to store user data
predictions_collection = db['predictions']

# Ensure Uploads Directory Exists
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Load ONNX model
model_path = os.path.join(os.getcwd(), "malaria_classification_model2.onnx")
try:
    session = ort.InferenceSession(model_path)
    LOG.info("Model loaded successfully.")
except Exception as e:
    LOG.error("Error loading model: %s", str(e))
    raise RuntimeError("Failed to load ONNX model.")

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home Page
@app.route("/")
def home():
    return render_template("index.html")

# Sign-Up Route
@app.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        email = request.form.get("email").strip()
        password1 = request.form.get("password1").strip()
        password2 = request.form.get("password2").strip()

        if password1 != password2:
            flash("Passwords do not match.", "error")
        elif len(password1) < 8:
            flash("Password must be at least 8 characters.", "error")
        elif users_collection.find_one({"email": email}):
            flash("Email already exists.", "error")
        else:
            hashed_password = generate_password_hash(password1)
            users_collection.insert_one({"email": email, "password": hashed_password})
            flash("Account created successfully!", "success")
            return redirect(url_for("login"))

    return render_template("sign_up.html")

# Login Route
@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form.get("email").strip()
        password = request.form.get("password").strip()

        user = users_collection.find_one({"email": email})
        if user and check_password_hash(user["password"], password):
            flask_session["user"] = email
            flask_session.permanent = True
            flash("Logged in successfully!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid email or password.", "error")

    return render_template("login.html")

# Logout Route
@app.route("/logout")
def logout():
    flask_session.pop("user", None)
    flask_session.pop("anonymous_attempts", None)
    flash("Logged out successfully.", "success")
    return redirect(url_for("home"))

# About Page
@app.route("/about")
def about():
    return render_template("about.html")

# Helpdesk Page
@app.route("/helpdesk")
def helpdesk():
    return render_template("helpdesk.html")

# FAQ Page
@app.route("/faq")
def faq():
    return render_template("faq.html")

# Limit Attempts for Anonymous Users
@app.before_request
def limit_anonymous_attempts():
    if request.endpoint == 'predict_route' and "user" not in flask_session:
        if "anonymous_attempts" not in flask_session:
            flask_session["anonymous_attempts"] = 0
        if flask_session["anonymous_attempts"] >= 5:
            flash("Free plan limit reached. Please sign in to continue.", "error")
            return redirect(url_for("login"))
        flask_session["anonymous_attempts"] += 1

# Preprocessing Function
def preprocess_image(image_path):
    image = cv2.imread(image_path)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    equalized_image = cv2.equalizeHist(gray_image)
    normalized_image = equalized_image / 255.0
    expanded_image = np.repeat(normalized_image[..., np.newaxis], 3, axis=-1)
    resized_image = cv2.resize(expanded_image, (224, 224))
    return np.expand_dims(resized_image, axis=0).astype(np.float32)

# Prediction Function
def predict_image(image_path):
    try:
        input_data = preprocess_image(image_path)
        input_name = session.get_inputs()[0].name
        prediction = session.run(None, {input_name: input_data})[0][0]

        result = "Parasitized" if prediction > 0.5 else "Uninfected"
        confidence = prediction if prediction > 0.5 else 1 - prediction

        return {"prediction": result, "confidence": float(confidence)}
    except Exception as e:
        LOG.error("Error during prediction: %s", str(e))
        return {"error": str(e)}

# Prediction Route
@app.route('/predict', methods=['POST'])
def predict_route():
    file = request.files.get('image')
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only PNG, JPG, or JPEG are allowed.'}), 400

    try:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        prediction_result = predict_image(file_path)

        with open(file_path, "rb") as image_file:
            file_id = fs.put(image_file, filename=file.filename)

        prediction_data = {
            'image_file_id': file_id,
            'image_filename': file.filename,
            'predicted_class': prediction_result["prediction"],
            'confidence': prediction_result["confidence"],
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        predictions_collection.insert_one(prediction_data)
        os.remove(file_path)

        return jsonify({
            'prediction': prediction_result["prediction"],
            'confidence': prediction_result["confidence"],
            'message': 'Prediction and image successfully saved to Database.'
        })

    except Exception as e:
        LOG.error("Error during prediction: %s", str(e))
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
