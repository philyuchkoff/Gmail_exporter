from __future__ import annotations

import os
import base64
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup
import pandas as pd

def _parse_date_folder(date_header: str) -> str:
    """Parse an RFC 2822 Date header into a YYYY-MM-DD folder name.

    Falls back to today's UTC date if the header is missing or unparseable
    so that attachments are still saved somewhere instead of crashing.
    """
    try:
        dt = parsedate_to_datetime(date_header)
    except (TypeError, ValueError):
        dt = None
    if dt is None:
        dt = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime('%Y-%m-%d')


def get_email_detail(service, msg_id, save_folder):
    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    payload = msg['payload']
    headers = payload['headers']

    subject = sender = recipient = date = ''
    for h in headers:
        if h['name'] == 'Subject':
            subject = h['value']
        elif h['name'] == 'From':
            sender = h['value']
        elif h['name'] == 'To':
            recipient = h['value']
        elif h['name'] == 'Date':
            date = h['value']

    parts = payload.get('parts', [])
    body = ''
    attachments = []

    for part in parts:
        if part['filename']:
            attachment_id = part['body']['attachmentId']
            data = service.users().messages().attachments().get(
                userId='me', messageId=msg_id, id=attachment_id).execute()
            file_data = base64.urlsafe_b64decode(data['data'].encode('UTF-8'))
            date_folder = _parse_date_folder(date)
            folder_path = os.path.join(save_folder, date_folder)
            os.makedirs(folder_path, exist_ok=True)
            filename = part['filename'].replace('/', '_').replace('\\', '_')

            filepath = os.path.join(folder_path, filename)
            with open(filepath, 'wb') as f:
                f.write(file_data)
            attachments.append(part['filename'])
        else:
            if part['mimeType'] == 'text/html':
                body = BeautifulSoup(base64.urlsafe_b64decode(part['body']['data']).decode(), 'html.parser').get_text()
            elif part['mimeType'] == 'text/plain':
                body = base64.urlsafe_b64decode(part['body']['data']).decode()

    return {
        'Date': date,
        'Sender': sender,
        'Recipient': recipient,
        'Subject': subject,
        'Body': body,
        'Attachments': ', '.join(attachments)
    }




def fetch_emails(service, query='', page_size=100, max_results=None):
    messages: list[dict] = []
    page_token: str | None = None

    while True:
        params: dict = {'userId': 'me', 'q': query, 'maxResults': page_size}
        if page_token:
            params['pageToken'] = page_token

        result = service.users().messages().list(**params).execute()
        messages.extend(result.get('messages', []))

        if max_results is not None and len(messages) >= max_results:
            return messages[:max_results]

        page_token = result.get('nextPageToken')
        if not page_token:
            break

    return messages

# Add this to the bottom of gmail_fetcher.py

import pandas as pd

def export_to_excel(email_data_list, output_file):
    df = pd.DataFrame(email_data_list)
    df.to_excel(output_file, index=False)

