# import re

# def extract_metadata(filename):
#     parts = filename.split("_")
#     location, date = None, None

#     # Find 8-digit date (like 20250113)
#     for p in parts:
#         if p.isdigit() and len(p) == 8:
#             date = p

#     # Try to find a likely location:
#     # - must be alphabetic (letters only)
#     # - not one of the known non-location words
#     # - and ideally appears near the start or middle
#     for p in parts:
#         if p.isalpha() and p not in ["M3T", "M350", "Ortho", "low", "high"]:
#             # Skip month names if followed by a proper name later
#             if p.lower() in ["january", "february", "march", "april",
#                              "may", "june", "july", "august", "september",
#                              "october", "november", "december"]:
#                 continue
#             location = p
#             break

#     # If still nothing found, mark as unknown
#     return location or "Unknown", date or "Unknown"

import re
from datetime import datetime
import csv
import os

def extract_metadata(filename):
    parts = filename.split("_")
    location, date_str, month_str = None, None, None

    # Detect an 8-digit date (e.g., 20250113)
    for p in parts:
        if p.isdigit() and len(p) == 8:
            date_str = p
            try:
                dt = datetime.strptime(date_str, "%Y%m%d")
                month_str = dt.strftime("%B")  # Convert numeric date to month name
            except ValueError:
                pass

    # Detect a month name (January, February, etc.)
    for p in parts:
        if p.lower() in ["january", "february", "march", "april", "may", "june",
                         "july", "august", "september", "october", "november", "december"]:
            month_str = p.capitalize()

    # Detect location: the first alphabetical word not in known tags
    ignore = {"M3T", "M350", "Ortho", "low", "high", "am", "pm"}
    for p in parts:
        if p.isalpha() and p not in ignore and p.lower() not in [m.lower() for m in ["January", "February", "March", "April", "May", "June",
                                                                                    "July", "August", "September", "October", "November", "December"]]:
            location = p
            break

    return location or "Unknown", date_str or "Unknown", month_str or "Unknown"



def log_to_csv(filename, bat_count, location, date_obj):
    # Define log file location
    log_file = "detections_log.csv"
    # Check if the file exists
    file_exists = os.path.exists(log_file)
    
    # Prepare data row
    row = {
        "filename": filename,
        "bat_count": bat_count,
        "location": location,
        "timestamp": date_obj.isoformat()  # UTC timestamp in ISO format
    }

    # Open file and write
    with open(log_file, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=row.keys())
        
        # Write header only if file doesn't exist
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(row)
