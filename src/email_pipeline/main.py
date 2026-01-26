import os
from pathlib import Path
from email_pipeline.client import IMAPClient
from email_pipeline.env import load_env
from email_pipeline.logger import logger
from email_pipeline.processor import process_message
from email_pipeline.state import load_last_uid, save_last_uid


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
        logger.info("Fetching messages since last UID", extra={"last_uid": last_uid})
        processed_uids = []
        fetched_uids = []
        for uid in client.fetch_unseen_since(last_uid):
            uid_num = int(uid)
            fetched_uids.append(uid_num)
            # BODY.PEEK[] so the server doesn't set the \Seen flag when returning the message
            _, data = client.conn.uid("fetch", uid, "(BODY.PEEK[])")
            if uid_num > last_uid:
                processed_uids.append(uid_num)
                process_message(data[0][1], os.getenv("ATTACHMENTS_DIR") or "attachments", uid.decode())
            highest_uid = max(highest_uid, uid_num)
            save_last_uid(state_path, highest_uid)
        logger.info("Finished processing messages",
                    extra={"new_last_uid": highest_uid, "fetched_uids": fetched_uids, "processed_uids": processed_uids})


def setup_env():
    env_path = Path(".env")
    env_vars = load_env(env_path)
    for key, value in env_vars.items():
        os.environ[key] = value


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        logger.exception(f"Unhandled exception: {e}", exc_info=True, stack_info=True)
