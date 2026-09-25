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


def _decode_part_data(data: str) -> str:
    """Decode a Gmail API part body data field (base64url encoded)."""
    return base64.urlsafe_b64decode(data.encode('UTF-8')).decode('utf-8', errors='replace')


def _walk_parts(service, msg_id, parts, attachments, body_state):
    """Recursively walk a Gmail message payload, collecting attachments and body.

    body_state is a dict with keys 'plain' and 'html'; plain wins over html
    when both are present.
    """
    for part in parts:
        filename = part.get('filename') or ''
        mime_type = part.get('mimeType', '')
        body = part.get('body') or {}

        if filename:
            attachment_id = body.get('attachmentId')
            if attachment_id:
                data = service.users().messages().attachments().get(
                    userId='me', messageId=msg_id, id=attachment_id
                ).execute()
                file_data = base64.urlsafe_b64decode(
                    data.get('data', '').encode('UTF-8')
                )
                yield part, filename, file_data
            continue

        if mime_type.startswith('multipart/'):
            nested = part.get('parts') or []
            yield from _walk_parts(service, msg_id, nested, attachments, body_state)
            continue

        part_data = body.get('data')
        if not part_data:
            continue

        if mime_type == 'text/plain' and not body_state['plain']:
            body_state['plain'] = _decode_part_data(part_data)
        elif mime_type == 'text/html' and not body_state['html']:
            body_state['html'] = BeautifulSoup(
                _decode_part_data(part_data), 'html.parser'
            ).get_text()


def get_email_detail(service, msg_id, save_folder):
    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    payload = msg['payload']
    headers = payload.get('headers', [])

    subject = sender = recipient = date = ''
    for h in headers:
        name = h.get('name', '')
        value = h.get('value', '')
        if name == 'Subject':
            subject = value
        elif name == 'From':
            sender = value
        elif name == 'To':
            recipient = value
        elif name == 'Date':
            date = value

    body_state: dict = {'plain': '', 'html': ''}
    attachments: list[str] = []
    nested = payload.get('parts') or []

    for part, filename, file_data in _walk_parts(
        service, msg_id, nested, attachments, body_state
    ):
        date_folder = _parse_date_folder(date)
        folder_path = os.path.join(save_folder, date_folder)
        os.makedirs(folder_path, exist_ok=True)
        safe_name = filename.replace('/', '_').replace('\\', '_')
        filepath = os.path.join(folder_path, safe_name)
        with open(filepath, 'wb') as f:
            f.write(file_data)
        attachments.append(filename)

    if not body_state['plain'] and not body_state['html'] and not nested:
        top_data = (payload.get('body') or {}).get('data')
        if top_data:
            mime_type = payload.get('mimeType', '')
            text = _decode_part_data(top_data)
            if mime_type == 'text/html':
                body_state['html'] = BeautifulSoup(text, 'html.parser').get_text()
            else:
                body_state['plain'] = text

    body = body_state['plain'] or body_state['html']

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


def export_to_excel(email_data_list, output_file):
    df = pd.DataFrame(email_data_list)
    df.to_excel(output_file, index=False)

