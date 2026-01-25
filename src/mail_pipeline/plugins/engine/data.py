from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class EmailContext:
    uid: str
    subject: str
    src: str
    dst: list[str]
    body_text: str
    attachments: list[Path]
    date: datetime | None
