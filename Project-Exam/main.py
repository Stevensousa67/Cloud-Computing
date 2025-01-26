import os
import base64
import secrets
import google.auth
from flask import Flask, request, render_template, redirect, url_for, flash, get_flashed_messages, session
from db import create, get
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

app = Flask(__name__)

# Set a secret key for session management from environment variable
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))

# Define your Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Load your client secret file from the environment variable
CLIENT_SECRET_FILE = os.environ.get('CLIENT_SECRET_FILE', 'Project-Exam/client_secrets.json')

@app.route('/', methods=['GET', 'POST'])
def add_todo():
    if request.method == 'POST':
        # Add a new ToDo to the database
        toDo = request.form.get('toDo')
        if toDo:
            try:
                create({'todo': toDo})
                flash('ToDo added successfully!', 'success')
            except Exception as e:
                flash(f"Failed to add ToDo: {str(e)}", 'danger')

        return redirect(url_for('add_todo'))
    else:
        flash_messages = get_flashed_messages(with_categories=True)
        return render_template('todo.html', flash_messages=flash_messages)

@app.route('/get', methods=['GET'])
def get_todos():
    return get()

@app.route('/send_email', methods=['GET'])
def send_email():
    # Check if the request is coming from Cloud Scheduler by inspecting the User-Agent header
    user_agent = request.headers.get('User-Agent', None)

    if user_agent == 'Google-Cloud-Scheduler':
        app.logger.info('Request is from Cloud Scheduler, using service account credentials...')
        
        # Automatically use App Engine's service account credentials
        credentials, project_id = google.auth.default(scopes=SCOPES)
    else:
        # This branch is for user-triggered requests, which require OAuth2 authorization
        if 'credentials' not in session:
            app.logger.info('No credentials in session, redirecting to /authorize...')
            return redirect(url_for('authorize'))  # Redirect to OAuth authorization

        # Load the user's credentials from the session
        credentials = Credentials(**session['credentials'])
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
    
    # If no valid credentials are found, use the refresh token method
    if not credentials or credentials.expired:
        try:
            refresh_token = os.environ.get('REFRESH_TOKEN')  # Load your refresh token from an environment variable
            credentials = Credentials(
                token=None,  # No need for access token here
                refresh_token=refresh_token,
                client_id=os.environ.get('CLIENT_ID'),
                client_secret=os.environ.get('CLIENT_SECRET'),
                token_uri='https://oauth2.googleapis.com/token'
            )
            credentials.refresh(Request())
        except Exception as e:
            app.logger.exception('Failed to refresh credentials using the refresh token.')
            return f"Failed to send email: {str(e)}", 500

    # Build the Gmail service with the obtained credentials
    service = build('gmail', 'v1', credentials=credentials)

    try:
        # Fetch the ToDos
        todos = get()
        app.logger.info(f'Fetched ToDos: {todos}')

        if not todos:  # Check if the list is empty
            app.logger.warning('No ToDos to send.')
            return 'No ToDos to send.', 200

        # Create the email message
        message = create_message(
            'cloud399v1@gmail.com',
            'silver.steven@hotmail.com',
            todos  # Pass the list of todos directly
        )

        # Send the email
        response = send_message(service, 'me', message)

        if response is None:
            app.logger.error('Failed to send email: No response received.')
            return 'Failed to send email: No response received.', 500

        app.logger.info(f'Email sent successfully! Response: {response}')
        return 'Email sent successfully!', 200
    except Exception as e:
        app.logger.exception('Exception occurred during email sending.')
        return f"Failed to send email: {str(e)}", 500

def create_message(sender, to, todos):
    """Create an email message to send via Gmail API."""
    
    # Format the ToDos as a string
    todos_content = "\n".join(f"- {todo['todo']}" for todo in todos)

    # Define the email body with your custom format
    message_text = (
        f"Hello,\n\n"
        f"This is from Steven Sousa.\n\n"
        f"Here is your To-Do-List:\n\n"
        f"{todos_content}\n"
        f"Thank you."
    )

    # Create the email with the static subject and encoded body
    message = {
        'raw': base64.urlsafe_b64encode(
            f"To: {to}\r\n"
            f"Subject: To Do List Reminder\r\n\r\n"
            f"{message_text}".encode('utf-8')
        ).decode('utf-8')
    }
    
    return message

def send_message(service, user_id, message):
    """Send an email using the Gmail API."""
    try:
        response = service.users().messages().send(userId=user_id, body=message).execute()
        if isinstance(response, dict) and 'id' in response:
            print(f'Message Id: {response["id"]}')
            return response
        else:
            print('Unexpected response format:', response)
            return None
    except Exception as e:
        print(f'An error occurred: {e}')
        return None

@app.route('/authorize')
def authorize():
    # Initiate OAuth2 flow for authorization
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    flow.redirect_uri = url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    
    session['state'] = state
    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES, state=state)
    flow.redirect_uri = url_for('oauth2callback', _external=True)

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    return redirect(url_for('send_email'))

def credentials_to_dict(credentials):
    """Convert OAuth credentials to a dictionary."""
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

if __name__ == '__main__':
    app.run(debug=True)