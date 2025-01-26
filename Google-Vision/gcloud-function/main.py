import functions_framework
from google.cloud import vision, storage
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import os
import io
import numpy as np


# Triggered by a change in a storage bucket
@functions_framework.cloud_event
def main(cloud_event):
    data = cloud_event.data

    bucket_name = data["bucket"]
    image_name = data["name"]

    # Skip processing for already boxed images
    if "__boxed.png" in image_name:
        return

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(image_name)

    detected_text = process_blob(blob, bucket)
    print(detected_text)  # This will print the detected text to the logs


def process_blob(blob, bucket):
    """Process an image blob from the storage bucket."""
    vision_client = vision.ImageAnnotatorClient()
    content = blob.download_as_bytes()
    image = vision.Image(content=content)

    # Perform OCR on the original image
    response = vision_client.document_text_detection(image=image)
    texts = response.text_annotations

    # If no text is detected, preprocess the image and retry OCR
    if not texts:
        preprocessed_image = preprocess_image_for_ocr(content)

        with io.BytesIO() as output:
            preprocessed_image.save(output, format="PNG")
            preprocessed_content = output.getvalue()

        preprocessed_image_vision = vision.Image(content=preprocessed_content)
        response = vision_client.document_text_detection(image=preprocessed_image_vision)
        texts = response.text_annotations

    # Draw bounding boxes if text is detected and upload boxed image
    if texts:
        processed_image_stream = draw_bounding_boxes(content, texts)
        upload_processed_image(processed_image_stream, blob, bucket)

    # Return the detected text
    detected_text = texts[0].description if texts else "No text detected"
    return detected_text


def preprocess_image_for_ocr(image_content):
    """Enhance the image for better OCR results."""
    with Image.open(io.BytesIO(image_content)) as img:
        gray_img = img.convert("L")
        blurred_img = gray_img.filter(ImageFilter.GaussianBlur(radius=1))
        contrasted_img = ImageEnhance.Contrast(blurred_img).enhance(2.0)

        # Convert to binary image
        img_array = np.array(contrasted_img)
        threshold = np.mean(img_array)
        binary_img = np.where(img_array > threshold, 255, 0).astype(np.uint8)

        # Convert back to PIL image
        processed_img = Image.fromarray(binary_img)

        # Sharpen the image
        sharpener = ImageEnhance.Sharpness(processed_img)
        sharpened_img = sharpener.enhance(2.0)

        return sharpened_img


def draw_bounding_boxes(image_content, texts):
    """Draw bounding boxes around detected text on the image."""
    with Image.open(io.BytesIO(image_content)) as img:
        draw = ImageDraw.Draw(img)

        # Draw bounding boxes for all detected text annotations except the first (full text)
        for text in texts[1:]:
            vertices = text.bounding_poly.vertices
            box = [(vertex.x, vertex.y) for vertex in vertices]
            draw.line(box + [box[0]], width=2, fill="red")

        output_stream = io.BytesIO()
        img.save(output_stream, format="PNG")
        output_stream.seek(0)

        return output_stream


def upload_processed_image(image_stream, blob, bucket):
    """Upload the processed image with bounding boxes to the storage bucket."""
    output_blob_name = f"{os.path.splitext(blob.name)[0]}__boxed.png"
    output_blob = bucket.blob(output_blob_name)

    output_blob.upload_from_file(image_stream, content_type="image/png")
    output_blob.make_public()
