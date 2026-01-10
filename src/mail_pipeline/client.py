import imaplib

class IMAPClient:
    def __init__(self, host, user, password, mailbox):
        self.host = host
        self.user = user
        self.password = password
        self.mailbox = mailbox

    def __enter__(self):
        self.conn = imaplib.IMAP4_SSL(self.host)
        self.conn.login(self.user, self.password)
        # Open mailbox in read-only mode so FETCH doesn't set the \Seen flag
        self.conn.select(self.mailbox, readonly=True)
        return self

    def __exit__(self, exc_type, exc, tb):
        self.conn.logout()

    def fetch_unseen_since(self, last_uid):
        status, data = self.conn.uid(
            "search", None, f"UID {last_uid+1}:* UNSEEN"
        )
        return data[0].split()
