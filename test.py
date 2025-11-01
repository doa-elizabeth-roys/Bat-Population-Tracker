# import os
# UPLOAD_FOLDER = "uploads"
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# print("Folder created successfully!")

# from APConv import PConv, APC2f
# print(PConv)

from ultralytics import YOLO
model = YOLO("best.pt")
print("YOLO imported successfully")

# test_import.py
# from ultralytics.nn.modules.APConv import PConv

# print(PConv)
