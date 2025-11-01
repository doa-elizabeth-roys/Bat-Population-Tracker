from flask import *
app = Flask(__name__)

import ultralytics
print(ultralytics.__version__)


@app.route('/')
def main():
    return render_template("index2.html")

def home():
    # Local image in static/images/SFF.png
    # image_url = url_for('static', filename='images/SFF.png') http://127.0.0.1:5000/static/images/SFF.png
    image_url = '../static/images/flyingbat.png'
    return render_template('index2.html', image_url=image_url)
    

@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':

        # Get the list of files from webpage
        files = request.files.getlist("file")

        # Iterate for each file in the files List, and Save them
        for file in files:
            file.save(file.filename)
        return "<h1>Files Uploaded Successfully.!</h1>"

# @app.post("/upload/")
# async def upload_image(file: UploadFile):
#     filepath = f"uploads/{file.filename}"
#     with open(filepath, "wb") as f:
#         shutil.copyfileobj(file.file, f)
#     results = run_inference(filepath)
#     publish_result_http(results)
#     return {"status": "ok", "bats": results["bat_count"]}



if __name__ == '__main__':
    app.run(debug=True)