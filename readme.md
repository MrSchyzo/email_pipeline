# `email_pipeline`: a simple python pipeline processing email from IMAP server

This is a python worker that executes custom python code to process emails from an IMAP server.

## What it does, in steps
1. Get the unseen emails since the last processed one (if a last is remembered)
1. For each one of them, extract sender, subject, date, text body, and attachments
1. Download the attachments in a dedicated folder, filenames will be prepended with the mail UID
1. Pass the extracted data to all custom python plugins
1. If all plugins are successfull, go to next unseen email
1. At the end, remember the last message UID

## Build
Requirements:
- Python `3.8+`

Run it locally after setting the correct .env variables
```bash
python3 -m venv venv
source venv/bin/python
pip install . && PYTHONPATH="$(pwd)/src" python src/mail_pipeline/main.py
```

Or, since no dependencies are currently needed, run the following at the repository's root:
```bash
PYTHONPATH="$(pwd)/src" python3 src/mail_pipeline/main.py
```

## Plugin mechanism

Plugins are named folders containing a `plugin.py` file and they do receive the email metadata via JSON stdin.

Plugins can have their own virtual enviroments: dependencies will be fetched by a `requirements.txt` file, while the virtual environment will be persisted in `plugin_envs/<plugin_dir_name>`.

To add a plugin just do the following:
1. add a folder in `plugins` named after the plugin name
1. add a `plugin.py` file that will be executed
1. expect the mail being passed in stdin as a json string with the following properties
    - `uid: uid` -> the email UID
    - `subject: str` -> the subject in UTF8
    - `src: str` -> the sender in UTF8
    - `dst: list[str]` -> the recipients in UTF8
    - `body_text: str` -> raw text in UTF8, can also be HTML
    - `attachments: list[str]` -> absolute paths of the downloaded attachments
    - `date: str | None` -> extracted datetime in ISO-8601 format
1. [optional] if dependencies are needed, add a `requirements.txt` file
1. [optional] environment variables for the script can be included in a `.env` file

Plugins are executed in parallel with no particular order for each unread email and they can do anything, including side effects.
To configure how many plugins are executed in parallel, set `PARALLELISM` environment variable to an integer value, default is 8.

Some examples are present in `plugins` folder.
