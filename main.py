import sys
import os
from extract import extract_metadata, log_to_csv
import requests
from werkzeug.utils import secure_filename
import cv2
import numpy as np


ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "tiff"}

sys.path.append("C:/Users/DALE MARY MATHEW/Downloads/ComputerVisionUpload")

from ultralytics.nn.modules.APConv import PConv
from ultralytics import YOLO

from google.cloud import storage
from google.oauth2 import service_account


# Load credentials from the JSON file in your project
credentials = service_account.Credentials.from_service_account_file(
    "bat-detection-project-9946198a7c2b.json"
)

# Create a storage client and bucket globally
storage_client = storage.Client(credentials=credentials)
bucket = storage_client.bucket("spectacaled-flying-fox-results")
# Path to your service account key
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"

# bucket = storage.Client(credentials=credentials).bucket("spectacaled-flying-fox-results")

# Initialize GCS client
# gcs_client = storage.Client()

# # Set your bucket name
# GCS_BUCKET_NAME = "spectacaled-flying-fox-results"  


from flask import *
app = Flask(__name__)

THINGSPEAK_API_KEY = "H0JZNIRA6SMHJNO8"
THINGSPEAK_URL = "https://api.thingspeak.com/update"
 
# Define directories
UPLOAD_FOLDER = "uploads"
RESULTS_FOLDER = "static/results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

model = YOLO("best.pt")


@app.route('/')
# def main():
#     return render_template("index.html")

def home():
    # Local image in static/images/SFF.png
    # image_url = url_for('static', filename='images/SFF.png') http://127.0.0.1:5000/static/images/SFF.png
    image_url = '../static/images/flyingbat.png'
    return render_template('index.html', image_url=image_url)
    

# @app.route('/upload', methods=['POST'])
# def upload():
#     if request.method == 'POST':

#         # Get the list of files from webpage
#         files = request.files.getlist("file")

#         # Iterate for each file in the files List, and Save them
#         for file in files:
#             file.save(file.filename)
#         return "<h1>Files Uploaded Successfully.!</h1>"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/upload", methods=["POST"])
def upload_files():
    message = None  # Initialize message at the start
    files = request.files.getlist("file")
    if not files:
        message = "No files uploaded!"
        return render_template("index.html", message=message)

    results_list = []
    total_bats = 0

    for file in files:
        filename = secure_filename(file.filename)

        def allowed_file(filename):
            return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
        
        # Check if it's an allowed file (image)
        if not allowed_file(filename):
            results_list.append({
                "filename": filename,
                "bat_count": "N/A",
                "location": "Unknown",
                "date": "N/A",
                "processed_image": None,
                "error": f"Unsupported file type: {filename.split('.')[-1]}"
            })
            continue  # Skip the processing for this non-image file

        # Process image files
        # img_path = os.path.join(UPLOAD_FOLDER, file.filename)
        # file.save(img_path)


        # 'file' is from request.files
        file_bytes = np.frombuffer(file.read(), np.uint8)  # read uploaded file into bytes
        img = cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)  # d

        results = model.predict(img, conf=0.25, save=False)
                                # project=RESULTS_FOLDER, name="processed")
        processed_img = results[0].plot()
        
        # import cv2
        # processed_filename = f"processed_{file.filename}"
        # processed_image_path = os.path.join(RESULTS_FOLDER, processed_filename)
        # cv2.imwrite(processed_image_path, processed_img)

# --- Upload directly to GCS from memory ---
        _, img_encoded = cv2.imencode('.jpg', processed_img)
        img_bytes = img_encoded.tobytes()

        blob = bucket.blob(f"results/processed_{filename}")  # GCS path
        blob.upload_from_string(img_bytes, content_type='image/jpeg')
        blob.make_public()
        processed_image_url = blob.public_url

        # detections = results[0].to_json()
        
        bat_count = len(results[0].boxes)
        total_bats += bat_count
        location, date_str, month = extract_metadata(file.filename)


        #Convert date string to ThingSpeak timestamp
        from datetime import datetime
        try:
            if len(date_str) == 8 and date_str.isdigit():
                # Handle filenames like 20240918
                date_obj = datetime.strptime(date_str, "%Y%m%d")
            elif "_" in date_str:
                # Handle filenames with timestamps like 2024-09-18_23-45
                date_obj = datetime.strptime(date_str, "%Y-%m-%d_%H-%M")
            elif any(month in date_str for month in [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]):
                # Handle names like January_20250113_...
                parts = date_str.split("_")
                for p in parts:
                    if p.isdigit() and len(p) == 8:
                        date_obj = datetime.strptime(p, "%Y%m%d")
                        break
                else:
                    raise ValueError
            else:
                raise ValueError
        except ValueError:
            date_obj = datetime.utcnow()
        # try:
        #     # assuming date is like "2024-06-18_23-45"
        #     date_obj = datetime.strptime(date_str, "%Y-%m-%d_%H-%M")
        # except ValueError:
        #     # fallback if format varies
        #     date_obj = datetime.utcnow()

        send_to_thingspeak(bat_count, location, date_obj)
        log_to_csv(filename, bat_count, location, date_obj,bucket)

        # Use GCS public URL for web display
        processed_image_url = blob.public_url
        # Build URL to show on web page
        # processed_image_url = url_for("static", filename=f"results/{processed_filename}")

        results_list.append({
            "filename": file.filename,
            "bat_count": bat_count,
            "location": location,
            "date": date_str,
            "processed_image": processed_image_url
        })

        # send_to_thingspeak(bat_count, location, date)

        # results_list.append({
        #     "filename": file.filename,
        #     "bat_count": bat_count,
        #     "location": location,
        #     "date": date,
        #     "processed_image": processed_image_data
        # })

        # Flask expects a URL relative to the static folder or server root
        # processed_image_url = url_for('static', filename=f"results/processed/{file.filename}")

        # results_list.append({
        #     "filename": file.filename,
        #     "bat_count": bat_count,
        #     "location": location,
        #     "date": date,
        #     "month": month
        # })

    # return jsonify({
    #     "message": "Detection completed and data sent to ThingSpeak!",
    #     "results": results_list
    # })
        # print(f"Image {file.filename}: {total_bats} bats detected at {location} on {date_str}")
        if len(files) == 1:
            message = f"Detected {total_bats} bats at {location}"
        else:
            message = f"Detected total {total_bats} bats across {len(files)} images"


    # Return HTML with message instead of JSON
    return render_template(
        "index.html",
        message = message,
        # message=f"{total_bats} bats detected at {location} on {date_str} and sent to ThingSpeak!",
        # processed_image=processed_image_url
        results = results_list

    )

def send_to_thingspeak(count, location="Unknown", date_obj=None):
    if date_obj is None:
        from datetime import datetime
        date_obj = datetime.utcnow()

    payload = {
        "api_key": THINGSPEAK_API_KEY,
        "field1": count,       # Bat count
        "field2": location,    # Location
        "created_at": date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")  # ISO UTC format  # Custom timestamp from filename
    }
    print("Uploading to ThingSpeak:", payload)

    try:
        response = requests.post("https://api.thingspeak.com/update.json", json=payload)
        print("ThingSpeak Response:", response.text)
    except Exception as e:
        print("ThingSpeak upload failed:", e)

    # print(f"Sending to ThingSpeak: {payload}")  # Debug


  
# def send_to_thingspeak(count, location="Unknown", date="Unknown"):
#     payload = {
#         "api_key": THINGSPEAK_API_KEY,
#         "field1": count,        # Bat count
#         "field2": location,     # Location name
#         "field3": date,         # Date
#     }
#     print(f"Sending to ThingSpeak: {payload}")  # debug line
#     try:
#         response = requests.post(THINGSPEAK_URL, params=payload)
#         # if response.status_code == 200:
#         print(f"ThingSpeak Response:", response.text)
#         # else:
#         #     print(f"ThingSpeak failed with status: {response.status_code}")
#     except Exception as e:
#         print(f"ThingSpeak upload failed: {e}")


if __name__ == '__main__':
    app.run(debug=True)
