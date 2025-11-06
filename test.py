# import os
# UPLOAD_FOLDER = "uploads"
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# print("Folder created successfully!")

# from APConv import PConv, APC2f
# print(PConv)

# from ultralytics import YOLO
# model = YOLO("best.pt")
# print("YOLO imported successfully")

# # test_import.py
# from ultralytics.nn.modules.APConv import PConv

# print(PConv)

import requests

THINGSPEAK_URL = "https://api.thingspeak.com/update"
THINGSPEAK_API_KEY = "H0JZNIRA6SMHJNO8"

payload = {
    "api_key": THINGSPEAK_API_KEY,
    "field1": 42,
    "field2": "Maalan",
    "field3": "20250121"
}

r = requests.post(THINGSPEAK_URL, params=payload)
print(r.status_code, r.text)  # Should print: 200 1
