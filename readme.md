## Build

Requirements:
- Python 3.9+

Run it locally after setting the correct .env variables
```bash
python3 -m venv venv
source venv/bin/python
pip install . && python src/mail_pipeline/main.py
```

Or, since no dependencies are currently needed, run the following at the repository's root:
```bash
PYTHONPATH="$(pwd)/src" python3 src/mail_pipeline/main.py
```
