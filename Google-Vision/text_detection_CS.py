import os, io
from google.cloud import vision, storage
from PIL import Image, ImageDraw

def text_finder(image_name=None):
    # Set the path to your Google Cloud service account credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'ServiceAccountToken.json'

    # Initialize the Google Vision API client
    vision_client = vision.ImageAnnotatorClient()
    storage_client = storage.Client()
    BUCKET_NAME = os.environ.get("BUCKET_NAME")

    # Get the bucket
    bucket = storage_client.bucket(BUCKET_NAME)

    # Process the specific image if provided
    blobs = [bucket.blob(image_name)] if image_name else bucket.list_blobs()

    for blob in blobs:
        if blob.name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', 'webp')):
            print(f'\nProcessing file: {blob.name}')

            # Read the image content from GCS
            content = blob.download_as_bytes()

            # Prepare the image for the Google Vision API
            image = vision.Image(content=content)

            # Perform text detection
            response = vision_client.document_text_detection(image=image)
            texts = response.text_annotations

            print('Texts:')
            
            if texts:
                # Print the detected text
                print(f'\n"{texts[0].description}"')

                # Load image into PIL for drawing
                image_stream = io.BytesIO(content)
                img = Image.open(image_stream)
                draw = ImageDraw.Draw(img)

                # Draw bounding boxes around detected text
                for text in texts[1:]:  # Skip the first element which is the entire text block
                    vertices = text.bounding_poly.vertices
                    box = [(vertex.x, vertex.y) for vertex in vertices]
                    draw.line(box + [box[0]], width=2, fill="red")

                # Prepare image for upload
                output_image_stream = io.BytesIO()
                img.save(output_image_stream, format='PNG')
                output_image_stream.seek(0)

                # Create a new blob for the output image with a modified name
                output_blob_name = f'{os.path.splitext(blob.name)[0]}_boxed.png'
                output_blob = bucket.blob(output_blob_name)

                # Upload the modified image to the bucket
                output_blob.upload_from_file(output_image_stream, content_type='image/png')
                print(f"Saved image with bounding boxes to {output_blob_name} in bucket {BUCKET_NAME}")
            
            else:
                print('No text found in the image.')

            # Check for any errors in the response
            if response.error.message:
                raise Exception(
                    '{}\nFor more info on error messages, check: '
                    'https://cloud.google.com/apis/design/errors'.format(
                        response.error.message))