from google.cloud import vision, storage
from PIL import Image, ImageDraw
import os, io, json

def detect_and_box_animals(request):
    """Detects animals, draws bounding boxes, saves the image to Cloud Storage, and returns results."""
    # Verify file in request
    if 'image' not in request.files:
        print("No file named 'image' in request")
        return {"error": "No image file provided"}, 400

    image_file = request.files['image']
    image_bytes = image_file.read()

    # Initialize Vision client
    client = vision.ImageAnnotatorClient()

    # Convert to Vision Image object
    image = vision.Image(content=image_bytes)

    # Perform object localization
    response = client.object_localization(image=image)
    if response.error.message:
        raise Exception(response.error.message)

    objects = response.localized_object_annotations

    # Create a PIL Image object
    pil_image = Image.open(io.BytesIO(image_bytes))
    draw = ImageDraw.Draw(pil_image)

    # Perform label detection
    response = client.label_detection(image=image)
    labels = response.label_annotations
    print(labels)

    results = []
    for label in labels:
        if "animal" in label.description.lower():  # Filter for animals
            results.append((label.description, label.score))
    
    for obj in objects:
        vertices = obj.bounding_poly.normalized_vertices
        box = [
            (int(vertex.x * pil_image.width), int(vertex.y * pil_image.height))
            for vertex in vertices
        ]
        draw.line(box + [box[0]], width=3, fill='red')
        results.append((obj.name, obj.score))

    # Save modified image to Cloud Storage
    storage_client = storage.Client()
    bucket_name = "comp399_final_project"
    blob_name = f"boxed_{os.urandom(10).hex()}.jpg"
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    output = io.BytesIO()
    pil_image.save(output, format="JPEG")
    output.seek(0)
    blob.upload_from_file(output, content_type="image/jpeg")

    # Make the image publicly accessible
    blob.make_public()
    image_url = f"https://storage.googleapis.com/{bucket_name}/{blob_name}"

    return {"results": results, "image_url": image_url}