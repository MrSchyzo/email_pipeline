import email
from pathlib import Path

from mail_pipeline.plugin_engine import EmailContext, execute_plugins

def process_message(raw_bytes, attachments_dir):
    msg = email.message_from_bytes(raw_bytes)
    subject = msg.get("Subject", "")
    sender = msg.get("From", "")

    attachments_dir = Path(attachments_dir)
    attachments_dir.mkdir(exist_ok=True)

    body_parts = []
    files = []
    for part in msg.walk():
        if part.get_content_type().startswith('text/'):
            body_parts = body_parts + [part.get_payload(decode=True).decode('utf-8', errors='ignore')]
        elif part.get_content_disposition() == "attachment":
            filename = part.get_filename()
            if filename:
                path = attachments_dir / filename
                path.write_bytes(part.get_payload(decode=True))
                files = files + [path.resolve()]
                
    context = EmailContext(
        subject=subject,
        src=sender,
        dst=msg.get_all("To", []),
        body_text="\n".join(body_parts),
        attachments=files,
        date=extract_email_date(msg)
    )
    
    execute_plugins(context)

    return True

def extract_email_date(msg):
    date_str = msg.get("date")
    if not date_str:
        return None
    return email.utils.parsedate_to_datetime(date_str)
