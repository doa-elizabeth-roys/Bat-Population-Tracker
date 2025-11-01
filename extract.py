import re

def extract_metadata(filename):
    parts = filename.split("_")
    location, date = None, None

    # Find 8-digit date (like 20250113)
    for p in parts:
        if p.isdigit() and len(p) == 8:
            date = p

    # Try to find a likely location:
    # - must be alphabetic (letters only)
    # - not one of the known non-location words
    # - and ideally appears near the start or middle
    for p in parts:
        if p.isalpha() and p not in ["M3T", "M350", "Ortho", "low", "high"]:
            # Skip month names if followed by a proper name later
            if p.lower() in ["january", "february", "march", "april",
                             "may", "june", "july", "august", "september",
                             "october", "november", "december"]:
                continue
            location = p
            break

    # If still nothing found, mark as unknown
    return location or "Unknown", date or "Unknown"
