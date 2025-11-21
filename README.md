# Automated Bat Detection and Counting Using Thermal Images

This project focuses on **computer vision** for **automated detection and counting of bats** using thermal images. The system uses **deep learning** models to detect bats in thermal images and displays predicted bounding boxes along with the bat count. Additionally, the web interface provides an embedded `thingSpeak` plot to visualize population trends over time. The bat count data, image metadata (including filenames and locations), and other relevant details are sent to **Google Cloud Services** for future analysis and storage.

## Features

- **Batch Image Upload:** Users can upload up to 60 thermal images or files at a time.
- **Image Display with Predicted Bounding Boxes:** Each uploaded image is processed, and the predicted bounding boxes for bats are displayed.
- This project can also **skip duplicated files** when same image is uploaded more than once.
- **Bat Count:** The system automatically counts the bats present in each image.
- **ThingSpeak Plot:** A `ThingSpeak` plot is embedded to show bat population trends over time. The plot can be viewed [here](https://thingspeak.mathworks.com/channels/3142218/charts/1?bgcolor=%23ffffff&color=%23d62020&dynamic=true&results=200&title=Bat+Population+Over+Time&type=spline&xaxis=Date&yaxis=Bat+Counts).
- **Google Cloud Integration:** Image metadata (including filenames, bat counts, and locations) are sent to Google Cloud for storage and analysis.

## Requirements
To run this project locally, you'll need:

- Python 3.7 or higher
- Flask (for web interface)
- **YOLOv8** (for bat detection using the custom-trained model)
- **Google Cloud Storage** (for storing image metadata and results)
- **ThingSpeak API** (for plotting trends)
- Necessary Python packages (listed in `requirements.txt`)

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/doa-elizabeth-roys/Bat-Population-Tracker.git
   cd Bat-Population-Tracker

2. Install the dependencies:

```pip install -r requirements.txt```


3. Set up Google Cloud Storage:

    Ensure you have a Google Cloud account.

    Create a Google Cloud Storage bucket where image metadata and other results will be uploaded.

    Set up access keys for authentication and ensure that your environment can access the Google Cloud Storage bucket.

4. Set up ThingSpeak for visualizing trends:

    * Create an account on ThingSpeak

    * Obtain your API key to use in the project.

5. Using Your Own Model:

    The ultralytics folder in this repository contains a custom-modified YOLOv8 model (best.pt) that was developed specifically for bat detection in thermal images.

    If you want to use your own trained model, replace the best.pt file in the ultralytics folder with your own model checkpoint.

    If you have a custom implementation or additional components integrated into your YOLOv8 model, you can clone your model folder and replace the contents of the ultralytics folder with your own project files.

6. Run the application:

    ```python main.py```


7. Access the web interface at http://localhost:5000/