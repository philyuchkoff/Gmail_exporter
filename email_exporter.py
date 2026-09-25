import logging
import sys
import traceback

from gmail_auth import authenticate_gmail
from gmail_fetcher import fetch_emails, get_email_detail, export_to_excel

logger = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
    )

    try:
        service = authenticate_gmail()
    except Exception:
        logger.error("Failed to authenticate with Gmail: %s", traceback.format_exc())
        return 1

    query = input("Enter Gmail search query (e.g., 'has:attachment after:2024/01/01'): ")
    messages = fetch_emails(service, query)
    logger.info("Found %d message(s).", len(messages))

    all_data: list[dict] = []
    failures = 0
    for index, msg in enumerate(messages, start=1):
        try:
            detail = get_email_detail(service, msg['id'], save_folder='attachments')
        except Exception:
            failures += 1
            logger.exception(
                "Failed to process message %d/%d (id=%s); skipping.",
                index, len(messages), msg.get('id'),
            )
            continue
        all_data.append(detail)

    output_file = 'emails_export.xlsx'
    try:
        export_to_excel(all_data, output_file)
    except Exception:
        logger.error("Failed to write Excel file '%s': %s", output_file, traceback.format_exc())
        return 1

    logger.info(
        "Exported %d message(s) to %s (%d failed).",
        len(all_data), output_file, failures,
    )
    return 0 if failures == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
