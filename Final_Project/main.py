from google.cloud import storage
from flask import Flask, request, render_template
import requests, io, os

app = Flask(__name__)

BUCKET_NAME = 'comp399_final_project'
PROJECT_ID = 'bridgewater-state-university'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/Users/steven/Documents/Software Engineering/Bridgewater State University/Cloud-Computing/Final_Project/ServiceAccountToken.json"
CLOUD_FUNCTION_URL = 'https://us-east1-bridgewater-state-university.cloudfunctions.net/animal-detection'  # Replace with your Cloud Function URL

def upload_image_to_gcs(image):
    """Uploads an image to Google Cloud Storage and returns the blob name."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(image.filename)
    blob.upload_from_file(io.BytesIO(image.read()), content_type=image.mimetype)

@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    image_url = None

    if request.method == "POST":
        image = request.files.get("image")
        if image:
            # Send the image file to the Cloud Function
            try:
                response = requests.post(CLOUD_FUNCTION_URL,files={'image': image})
                response = response.json()
                print(f"Response: {response}")

                if 'results' in response:
                    results = response['results']
                    image_url = response['image_url']
                else:
                    print(f"Error: 'results' not found in response: {response}")
            except requests.exceptions.RequestException as e:
                print(f"Error sending request: {e}")
    
    return render_template("upload.html", results=results, image_url=image_url)

if __name__ == '__main__':
    app.run(debug=True)