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


from google.cloud import storage

def log_to_csv(filename, bat_count, location, date_obj, bucket):
    import csv
    import io
    from google.api_core.exceptions import NotFound

    gcs_path = "logs/detections_log.csv"
    blob = bucket.blob(gcs_path)

    # Try to download existing CSV if it exists
    try:
        existing_data = blob.download_as_text()
        file_exists = True
    except NotFound:
        existing_data = ""
        file_exists = False

     # Load existing filenames to skip duplicates
    existing_filenames = set()
    if file_exists and existing_data.strip():
        reader = csv.DictReader(io.StringIO(existing_data))
        for r in reader:
            existing_filenames.add(r["filename"])

    # Skip if this file is already logged
    if filename in existing_filenames:
        print(f"{filename} already exists. Skipping...")
        return

      # Prepare row
    row = {
        "filename": filename,
        "bat_count": bat_count,
        "location": location,
        "timestamp": date_obj.isoformat()
    }

    # Create an in-memory string buffer
    output = io.StringIO()

    # If file exists, copy the old data first
    if file_exists:
        output.write(existing_data)
        output.seek(0, io.SEEK_END)

    # Move cursor to end and write new data
    writer = csv.DictWriter(output, fieldnames=row.keys())

    # Write header only once if the file was empty
    if not file_exists:
        writer.writeheader()

    writer.writerow(row)

    # Upload updated CSV to GCS
    blob.upload_from_string(output.getvalue(), content_type="text/csv")
    output.close()
