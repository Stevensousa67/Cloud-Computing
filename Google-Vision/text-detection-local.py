import os, io
from google.cloud import vision

# Set the path to your Google Cloud service account credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'ServiceAccountToken.json'

# Initialize the Google Vision API client
client = vision.ImageAnnotatorClient()

# Path to the images directory
images_directory = 'Text Images'

# List all files in the images directory
for file_name in os.listdir(images_directory):
    # Construct the full path of the image file
    full_file_path = os.path.join(images_directory, file_name)

    # Check if the path is a file
    if os.path.isfile(full_file_path):
        print(f'\nProcessing file: {file_name}')

        # Read the image file
        with io.open(full_file_path, 'rb') as image_file:
            content = image_file.read()

        # Prepare the image for the Google Vision API
        image = vision.Image(content=content)

        # Perform text detection
        response = client.document_text_detection(image=image)
        texts = response.text_annotations

        print('Texts:')

        # Check if any text annotations were found
        if texts:
            # Print the text found in the image to terminal
            print(f'\n"{texts[0].description}"')

            # Create Results directory, if it doesn't exist
            output_directory = 'Results - Text'
            os.makedirs(output_directory, exist_ok=True)  # Create the directory if it doesn't exist
            
            # Save the text to a file named after the base name of the image file (without extension)
            output_file = os.path.join(output_directory, f'{os.path.splitext(file_name)[0]}.txt')
            with open(output_file, 'w') as file:
                file.write(texts[0].description)
        else:
            print('No text found in the image.')

        # Check for any errors in the response
        if response.error.message:
            raise Exception(
                '{}\nFor more info on error messages, check: '
                'https://cloud.google.com/apis/design/errors'.format(
                    response.error.message))