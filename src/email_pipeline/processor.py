import email
import os.path
import time
from mailbox import Message
from pathlib import Path

from email_pipeline.plugins.engine.execution import execute_plugins
from email_pipeline.plugins.engine.data import EmailContext
from email_pipeline.logger import logger


def process_message(raw_bytes: bytes | bytearray, attachments_dir: str, uid: str) -> bool:
    msg = email.message_from_bytes(raw_bytes)
    subject = decode_as_utf_8(msg.get("Subject", ""))
    sender = decode_as_utf_8(msg.get("From", ""))
    date = extract_email_date(msg)

    attachments_dir = Path(attachments_dir)
    attachments_dir.mkdir(exist_ok=True)

    body_parts = []
    files = []
    for part in msg.walk():
        if part.get_content_type().startswith('text/'):
            body_parts.append(part.get_payload(decode=True).decode('utf-8', errors='ignore'))
        elif part.get_content_disposition() == "attachment":
            filename = os.path.basename(decode_as_utf_8(part.get_filename()))
            if filename:
                path = attachments_dir / f'{uid}_{filename}'
                path.write_bytes(part.get_payload(decode=True))
                files = files + [path.resolve()]

    context = EmailContext(
        uid=uid,
        subject=subject,
        src=sender,
        dst=[decode_as_utf_8(x) for x in msg.get_all("To", [])],
        body_text="\n".join(body_parts),
        attachments=files,
        date=date
    )

    start = time.perf_counter_ns()
    try:
        logger.info(
            "Processing message",
            extra={"uid": uid, "date": date, "sender": sender, "subject": subject, "attachments_count": len(files)},
        )
        execute_plugins(context)
    finally:
        logger.debug("Cleaning out attachments", extra={"uid": uid, "attachments": files})
        for f in files:
            f.unlink()
    elapsed = (time.perf_counter_ns() - start)/1e6

    logger.info(
        "Finished processing message",
        extra={"elapsed_ms": elapsed, "uid": uid, "date": date, "sender": sender, "subject": subject,
               "attachments_count": len(files)}
    )

    return True


def decode_as_utf_8(raw_header: str | None) -> str | None:
    if raw_header is None:
        return None
    decoded_parts = email.header.decode_header(raw_header)
    return ''.join(
        text.decode(charset or 'utf-8') if isinstance(text, bytes) else text
        for text, charset in decoded_parts
    )


def decode_part_as_utf_8(part: Message) -> str:
    charset = part.get_content_charset() or 'utf-8'
    part.get_payload(decode=True).decode(charset, errors='ignore')


def extract_email_date(msg: Message):
    date_str = msg.get("date")
    if not date_str:
        return None
    return email.utils.parsedate_to_datetime(date_str)
