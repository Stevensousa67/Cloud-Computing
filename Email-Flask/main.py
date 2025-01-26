import os, base64, secrets
from flask import Flask, request, render_template, redirect, url_for, flash, get_flashed_messages, session
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

app = Flask(__name__)

# Set a secret key for session management from environment variable
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))  # Generates a secure random string if not set

# Define your Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Load your client secret file from the environment variable
CLIENT_SECRET_FILE = os.environ.get('CLIENT_SECRET_FILE', 'Email-Flask/client_secret.json')


@app.route('/send-email', methods=['GET', 'POST'])
def send_email():
    if request.method == 'POST':
        if 'credentials' not in session:
            return redirect(url_for('authorize'))

        # Retrieve the credentials from the session
        credentials = Credentials(**session['credentials'])
        
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        service = build('gmail', 'v1', credentials=credentials)

        try:
            # Create the email content
            message = create_message('cloud399v1@gmail.com',
                                     request.form.get('mailto'),
                                     request.form.get('subject'),
                                     request.form.get('message'))
            
            # Send the email
            send_message(service, 'me', message)
            
            flash('Email sent successfully', 'success')
        except Exception as e:
            flash("Failed to send email: " + str(e), "danger")
        
        return redirect(url_for('send_email'))  # Redirect to clear the form
    else:
        flash_messages = get_flashed_messages(with_categories=True)
        return render_template('send_email_form.html', flash_messages=flash_messages)


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/authorize')
def authorize():
    # Initiate OAuth2 flow for authorization
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    print("URL:", url_for('oauth2callback', _external=True))
    flow.redirect_uri = url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    
    session['state'] = state
    return redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    state = session['state']
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES, state=state)
    print("URL:", url_for('oauth2callback', _external=True))
    flow.redirect_uri = url_for('oauth2callback', _external=True)

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    return redirect(url_for('send_email'))


def create_message(sender, to, subject, message_text):
    """Create an email message to send via Gmail API."""
    message = {
        'raw': base64.urlsafe_b64encode(
            f'To: {to}\r\n'
            f'Subject: {subject}\r\n\r\n'
            f'{message_text}'.encode('utf-8')
        ).decode('utf-8')
    }
    return message


def send_message(service, user_id, message):
    """Send an email using the Gmail API."""
    try:
        message = service.users().messages().send(userId=user_id, body=message).execute()
        print(f'Message Id: {message["id"]}')
        return message
    except Exception as e:
        print(f'An error occurred: {e}')
        return None


def credentials_to_dict(credentials):
    """Convert OAuth credentials to a dictionary."""
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}

if __name__ == '__main__':
    app.run()