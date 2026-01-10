import os
from dotenv import load_dotenv
from mail_pipeline.client import IMAPClient
from mail_pipeline.processor import process_message
from mail_pipeline.state import load_last_uid, save_last_uid

def main():
    state_path = os.getenv("STATE_FILE") or "state/last_uid.txt"
    
    load_dotenv()

    last_uid = load_last_uid(state_path)
    highest_uid = last_uid

    with IMAPClient(
        os.getenv("IMAP_HOST"),
        os.getenv("IMAP_USER"),
        os.getenv("IMAP_PASS"),
        os.getenv("MAILBOX"),
    ) as client:

        for uid in client.fetch_unseen_since(last_uid):
            # BODY.PEEK[] so the server doesn't set the \Seen flag when returning the message
            _, data = client.conn.uid("fetch", uid, "(BODY.PEEK[])")
            process_message(data[0][1], os.getenv("ATTACHMENTS_DIR") or "attachments")
            highest_uid = max(highest_uid, int(uid))

    save_last_uid(state_path, highest_uid)

if __name__ == "__main__":
    main()
