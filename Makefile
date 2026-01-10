VENV=venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

.PHONY: venv install build clean

venv:
	python3 -m venv $(VENV)

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install .

build: install
	$(PIP) install pyinstaller
	$(VENV)/bin/pyinstaller --onefile src/mail_pipeline/main.py

clean:
	rm -rf $(VENV) build dist __pycache__
