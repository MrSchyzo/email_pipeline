# enforce linux/amd64 due to selenium/chromium compatibility issue: 
# Unsupported platform/architecture combination linux/aarch64 (See selenium's `selenium_manager.py:94` for more details)
FROM --platform=amd64 python:3.13-slim
WORKDIR /app
# This is VERY heavy: consider running the command without docker
RUN apt update && apt install -y chromium chromium-driver
RUN mkdir -p plugin_envs && mkdir -p attachments && mkdir -p state
COPY src/ ./src/
COPY plugins/ ./plugins/
COPY .env .env
ENV PYTHONPATH="/app/src"
CMD ["python", "src/mail_pipeline/main.py"]