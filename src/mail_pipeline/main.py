import os
from pathlib import Path
from mail_pipeline.client import IMAPClient
from mail_pipeline.env import load_env
from mail_pipeline.processor import process_message
from mail_pipeline.state import load_last_uid, save_last_uid

def main():
    state_path = "state/last_uid.txt"

    setup_env()    

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
            if int(uid) > last_uid:
                process_message(data[0][1], os.getenv("ATTACHMENTS_DIR") or "attachments", uid.decode())
            highest_uid = max(highest_uid, int(uid))

    save_last_uid(state_path, highest_uid)
    
def setup_env():
    env_path = Path(".env")
    env_vars = load_env(env_path)
    for key, value in env_vars.items():
        os.environ[key] = value

if __name__ == "__main__":
    main()
