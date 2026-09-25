# 📧 Gmail Email Exporter

A Python utility that connects to a Gmail account over OAuth 2.0, fetches
messages matching a search query, downloads any attachments, and exports the
collected metadata to an Excel workbook.

The script is intentionally small and modular — three files:

- `gmail_auth.py` — OAuth 2.0 authentication and token persistence
- `gmail_fetcher.py` — Gmail API access (search, payload parsing, Excel export)
- `email_exporter.py` — entry point that ties everything together

---

## 🚀 Features

- 🔍 Search Gmail with the standard query syntax (`from:`, `has:attachment`,
  `after:`, `before:`, `subject:`, `label:`, …)
- 📎 Download attachments, organised in `attachments/<YYYY-MM-DD>/`
- 📊 Export one row per message to an Excel workbook with date, sender,
  recipient, subject, body and the list of attachments
- 🔐 OAuth 2.0 with automatic refresh and safe JSON token storage
- 🛠️ Simple, dependency-light script that runs from the command line

---

## 📸 Demo

```bash
$ python email_exporter.py
Enter Gmail search query (e.g., 'has:attachment after:2024/01/01'): from:boss@example.com after:2024/01/01
2025-01-02 12:00:00 INFO Found 12 message(s).
2025-01-02 12:00:05 INFO Exported 12 message(s) to emails_export.xlsx (0 failed).
```

---

## 🧰 Requirements

- Python 3.7 or newer
- A Google account with the Gmail API enabled (see *Setup* below)
- The Python packages listed in `requirement.txt`

```bash
pip install -r requirement.txt
```

---

## 🛠️ Setup

1. **Enable the Gmail API**
   - Open the [Google Cloud Console](https://console.cloud.google.com/),
     create (or select) a project, and enable the *Gmail API*.
2. **Create OAuth client credentials**
   - Go to *APIs & Services → Credentials*, create an *OAuth client ID* of
     type *Desktop app*, and download the JSON.
   - Save it as `credentials.json` in the project root (or point
     `GMAIL_CREDENTIALS_FILE` at any other path).
3. **Run the script**

   ```bash
   python email_exporter.py
   ```

   The first run opens a browser window for Google sign-in. The resulting
   access/refresh token is persisted to `token.json` for subsequent runs.
   Override the path with the `GMAIL_TOKEN_FILE` environment variable.

---

## 🔎 Gmail Search Query Examples

| Query                                   | Description                          |
| --------------------------------------- | ------------------------------------ |
| `from:boss@example.com`                 | Messages from a specific sender      |
| `has:attachment`                        | Messages with attachments            |
| `after:2024/01/01 before:2024/12/31`    | Messages in a date range             |
| `subject:"Interview Update"`            | Messages with a specific subject     |
| `label:important`                       | Messages marked as important         |

Any combination of the operators above is supported — the value is passed
verbatim to `users().messages().list(q=…)`.

---

## 📂 Output

After a successful run you get two things in the project root:

```
emails_export.xlsx              # one row per message: date, sender, recipient,
                                # subject, body, attachments
attachments/
└── 2025-05-01/
    └── Interview_Confirmation.pdf
└── 2025-05-03/
    └── Feedback_Response.docx
```

- The Excel file is created in the current working directory. Attachments are
  grouped into folders named after the message date (`YYYY-MM-DD`); if the
  `Date` header is missing or unparseable, today's UTC date is used instead.

---

## ⚙️ Configuration

| Environment variable      | Purpose                                          | Default            |
| ------------------------- | ------------------------------------------------ | ------------------ |
| `GMAIL_CREDENTIALS_FILE`  | Path to the OAuth client secrets JSON            | `credentials.json` |
| `GMAIL_TOKEN_FILE`        | Path used to persist the access/refresh token    | `token.json`       |

---

## 🔐 Security Notes

- **Never** commit `credentials.json` or `token.json` — both are listed in
  `.gitignore`. Rotate the OAuth client and revoke the token if either leaks.
- The access/refresh token is stored as plain JSON (not pickle) using
  `google.oauth2.credentials.Credentials.to_json()`.
- The Gmail scope requested is read-only: `gmail.readonly`.

---

## 🧑‍💻 Author

Khushi Gupta

---

## 🙌 Acknowledgements

- Google for the Gmail API and the Python client libraries
- The Python open-source community
