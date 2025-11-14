import sys
import os
from extract import extract_metadata, log_to_csv
import requests
from werkzeug.utils import secure_filename
import cv2
import numpy as np


ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "tiff"}

# sys.path.append("C:/Users/DALE MARY MATHEW/Downloads/ComputerVisionUpload")

from ultralytics.nn.modules.APConv import PConv
from ultralytics import YOLO

from google.cloud import storage
from google.oauth2 import service_account


# Load credentials from the JSON file in your project
credentials = service_account.Credentials.from_service_account_file(
    "bat-detection-project-903753b6d424.json"
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

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # allow larger upload sizes
app.config['MAX_FILE_LENGTH'] = 5 * 1024 * 1024
app.config['MAX_FILES'] = 50

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
    files = request.files.getlist("file")
    if not files:
        return render_template("index.html", message="No files uploaded!")

    if len(files) > app.config['MAX_FILES']:
        return render_template("index.html", message=f"Maximum {app.config['MAX_FILES']} files allowed per upload")

    results_list = []
    total_bats = 0

    # ======  Load or create CSV from GCS ======
    gcs_path = "logs/detections_log.csv"
    blob = bucket.blob(gcs_path)

    try:
        existing_data = blob.download_as_text()
        file_exists = True
    except Exception:
        existing_data = ""
        file_exists = False

    # Track already-logged filenames to skip duplicates
    existing_filenames = set()
    if file_exists and existing_data.strip():
        import io, csv
        reader = csv.DictReader(io.StringIO(existing_data))
        for r in reader:
            existing_filenames.add(r["filename"])

    # Prepare new CSV buffer in memory
    import io, csv
    output = io.StringIO()
    if file_exists:
        output.write(existing_data)
        output.seek(0, io.SEEK_END)

    writer = csv.DictWriter(output, fieldnames=["filename", "bat_count", "location", "timestamp"])
    if not file_exists:
        writer.writeheader()

    # ======  Process files ======
    for file in files:
        filename = secure_filename(file.filename)

        if not allowed_file(filename):
            results_list.append({
                "filename": filename,
                "bat_count": "N/A",
                "location": "Unknown",
                "date": "N/A",
                "processed_image": None,
                "error": "Unsupported file type"
            })
            continue

        # Skip duplicates
        if filename in existing_filenames:
            print(f"{filename} already exists — skipping detection + ThingSpeak")
            continue

        # Decode uploaded image
        file_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)

        # Run model
        results = model.predict(img, conf=0.25, save=False)
        processed_img = results[0].plot()

        # Upload processed image to GCS
        _, img_encoded = cv2.imencode('.jpg', processed_img)
        blob_img = bucket.blob(f"results/processed_{filename}")
        blob_img.upload_from_string(img_encoded.tobytes(), content_type='image/jpeg')
        blob_img.make_public()
        processed_image_url = blob_img.public_url

        # Extract metadata (you already have extract_metadata)
        location, date_str, month = extract_metadata(filename)
        from datetime import datetime
        try:
            if len(date_str) == 8 and date_str.isdigit():
                date_obj = datetime.strptime(date_str, "%Y%m%d")
            elif "_" in date_str:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d_%H-%M")
            else:
                date_obj = datetime.utcnow()
        except ValueError:
            date_obj = datetime.utcnow()

        # Get detection info
        bat_count = len(results[0].boxes)
        total_bats += bat_count

        # Add to CSV only for new file
        writer.writerow({
            "filename": filename,
            "bat_count": bat_count,
            "location": location,
            "timestamp": date_obj.isoformat()
        })

        # Send to ThingSpeak only for new files
        send_to_thingspeak(bat_count, location, date_obj)

        # Save result for web display
        results_list.append({
            "filename": filename,
            "bat_count": bat_count,
            "location": location,
            "date": date_str,
            "processed_image": processed_image_url
        })

    # ====== Upload final CSV to GCS once ======
    blob.upload_from_string(output.getvalue(), content_type="text/csv")
    output.close()

    # ====== Web response ======
    if len(results_list) == 0:
        message = "All uploaded files already exist in the database — nothing new processed."
    elif len(results_list) == 1:
        message = f"Detected {total_bats} bats at {results_list[0]['location']}"
    else:
        message = f"Processed {len(results_list)} new images — total {total_bats} bats detected!"

    return render_template("index.html", message=message, results=results_list)


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
