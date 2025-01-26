import os, io
from PIL import Image, ImageDraw
from google.cloud import vision

# Set the path to your Google Cloud service account credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'ServiceAccountToken.json'

# Initialize the Google Vision API client
client = vision.ImageAnnotatorClient()

# text_images_directory = 'Text Images'
face_images_directory = 'Face Images'

# List all files in the images directory
for file_name in os.listdir(face_images_directory):
    # Construct the full path of the image file
    full_file_path = os.path.join(face_images_directory, file_name)

    # Check if the path is a file
    if os.path.isfile(full_file_path):
        print(f'\nProcessing file: {file_name}')

        # Read the image file
        with io.open(full_file_path, 'rb') as image_file:
            content = image_file.read()

        # Prepare the image for the Google Vision API
        image = vision.Image(content=content)
        
        # Perform face detection
        face_response = client.face_detection(image=image)
        faces = face_response.face_annotations

        if faces:
            print('\nFaces found:')

            # Load the original image using PIL
            with Image.open(full_file_path) as img:
                draw = ImageDraw.Draw(img)

                for i, face in enumerate(faces):
                    print(f' - Face {i+1}:')
                    print(f'   - Joy: {face.joy_likelihood}')
                    print(f'   - Anger: {face.anger_likelihood}')
                    print(f'   - Sorrow: {face.sorrow_likelihood}')
                    print(f'   - Surprise: {face.surprise_likelihood}')

                    # Draw a rectangle around the face
                    vertices = face.bounding_poly.vertices
                    if len(vertices) == 4:
                        # Define the bounding box
                        top_left = (vertices[0].x, vertices[0].y)
                        bottom_right = (vertices[2].x, vertices[2].y)
                        draw.rectangle([top_left, bottom_right], outline="red", width=3)

                        print(f'   Bounding box drawn from {top_left} to {bottom_right}')

                output_directory = 'Results - Faces'
                os.makedirs(output_directory, exist_ok= True)

                # Save the modified image with a rectangle
                modified_image_path = os.path.join(output_directory, f'{os.path.splitext(file_name)[0]}_faces.jpg')
                img.save(modified_image_path)
                print(f'Saved modified image with face bounding boxes as: {modified_image_path}')
        else:
            print('No faces found in the image.')

        # Check for any errors in both responses
        if face_response.error.message:
            raise Exception(
                '{}\nFor more info on error messages, check: '
                'https://cloud.google.com/apis/design/errors'.format(
                    face_response.error.message))