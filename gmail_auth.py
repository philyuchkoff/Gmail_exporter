import json
import os
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

CREDENTIALS_FILE = os.environ.get('GMAIL_CREDENTIALS_FILE', 'credentials.json')
TOKEN_FILE = os.environ.get('GMAIL_TOKEN_FILE', 'token.json')


def _load_existing_credentials() -> Optional[Credentials]:
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        return Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    except (ValueError, json.JSONDecodeError):
        return None


def authenticate_gmail():
    creds = _load_existing_credentials()

    if creds and creds.valid:
        return build('gmail', 'v1', credentials=creds)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        if not os.path.exists(CREDENTIALS_FILE):
            raise FileNotFoundError(
                f"OAuth client secrets not found: '{CREDENTIALS_FILE}'. "
                "Enable the Gmail API in Google Cloud Console and download the "
                "credentials JSON, or set GMAIL_CREDENTIALS_FILE to its path."
            )
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)
