import sys
import os
import extract_metadata
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

sys.path.append("C:/Users/DALE MARY MATHEW/Downloads/ComputerVisionUpload")

from ultralytics.nn.modules.APConv import PConv
from ultralytics import YOLO


from flask import *
app = Flask(__name__)

THINGSPEAK_API_KEY = "H0JZNIRA6SMHJNO8"
THINGSPEAK_URL = "https://api.thingspeak.com/update"
 
# Define directories
UPLOAD_FOLDER = "uploads"
RESULTS_FOLDER = "results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

model = YOLO("best.pt")


@app.route('/')
def main():
    return render_template("index.html")

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

@app.route("/upload", methods=["POST"])
def upload_files():
    files = request.files.getlist("file")  # multiple files
    results_list = []

    if not files:
        return jsonify({"error": "No files uploaded!"}), 400

    for file in files:
        img_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(img_path)

        # Run inference on each image
        results = model.predict(img_path, conf=0.25)
        detections = results[0].tojson()

        # Count detections
        bat_count = len(results[0].boxes)

        # Extract metadata from filename
        location, date = extract_metadata(file.filename)

        # Send to ThingSpeak
        send_to_thingspeak(bat_count, location, date)

        # Store or send detections
        # results_list.append({
        #     "filename": file.filename,
        #     "detections": detections
        # })

        # (Optional) publish_to_cloud(detections)

    # return jsonify(results_list)
    return jsonify({
    "message": "Detection completed and data sent to ThingSpeak!",
    "filename": file.filename,
    "bat_count": bat_count
    })



# @app.post("/upload/")
# async def upload_image(file: UploadFile):
#     filepath = f"uploads/{file.filename}"
#     with open(filepath, "wb") as f:
#         shutil.copyfileobj(file.file, f)
#     results = run_inference(filepath)
#     publish_result_http(results)
#     return {"status": "ok", "bats": results["bat_count"]}

def send_to_thingspeak(count, location="Unknown", date="Unknown"):
    payload = {
        "api_key": THINGSPEAK_API_KEY,
        "field1": Bat Counts,        # Bat count
        "field2": location,     # Location name
        "field3": date,         # Date (YYYYMMDD or readable format)

    }
    try:
        response = requests.post(THINGSPEAK_URL, params=payload)
        print("Sent to ThingSpeak:", response.text)
    except Exception as e:
        print("ThingSpeak upload failed:", e)


if __name__ == '__main__':
    app.run(debug=True)