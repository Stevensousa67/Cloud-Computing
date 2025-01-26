from time import sleep
from flask import Flask, request, render_template
from google.cloud import storage, vision
import os, io

app = Flask(__name__)

# Initialize Google Cloud Storage client
# BUCKET_NAME = os.environ.get("BUCKET_NAME")
# PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
BUCKET_NAME = 'bridgewater-state-university.appspot.com'
PROJECT_ID = 'bridgewater-state-university'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'ServiceAccountToken.json'
storage_client = storage.Client()

def upload_image_to_gcs(image):
    """Uploads an image to Google Cloud Storage and returns the blob name."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(image.filename)
    blob.upload_from_file(
        io.BytesIO(image.read()), content_type=image.mimetype
    )


def wait_for_processed_image(filename, retries=10, interval=1):
    """Waits for the processed image to appear in the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    processed_filename = f"{os.path.splitext(filename)[0]}__boxed.png"

    for _ in range(retries):
        blob = bucket.blob(processed_filename)
        if blob.exists():
            return f"https://storage.googleapis.com/{BUCKET_NAME}/{processed_filename}"
        sleep(interval)
    return None

def get_extracted_text(filename):
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)

    if blob.exists():
        content = blob.download_as_bytes()
        vision_client = vision.ImageAnnotatorClient()
        image = vision.Image(content=content)
        response = vision_client.document_text_detection(image=image)
        texts = response.text_annotations

        if texts:
          return texts[0].description  # returns all detected text
    return "No text detected" # returns if no text found


@app.route("/", methods=["GET", "POST"])
def home():
    """Handles file upload and checks for processed image."""
    processed_image_url = None
    extracted_text = None

    if request.method == "POST":
        image = request.files.get("image")

        if image:
            # Upload the image to Google Cloud Storage
            upload_image_to_gcs(image)

            # Wait for the processed image to appear in the bucket
            processed_image_url = wait_for_processed_image(image.filename)
            extracted_text = get_extracted_text(image.filename)

    return render_template("upload.html", processed_image_url=processed_image_url, extracted_text=extracted_text)


if __name__ == '__main__':
    app.run(debug=True)