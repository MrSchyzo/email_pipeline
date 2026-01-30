# enforce linux/amd64 due to selenium/chromium compatibility issue: 
# Unsupported platform/architecture combination linux/aarch64 (See selenium's `selenium_manager.py:94` for more details)
FROM --platform=amd64 python:3.13-slim
WORKDIR /app
# This is VERY heavy: consider running the command without docker
# For gui stuff, xvfb would be needed: prepend `xvfb-run` to the command in such case
RUN apt update && apt install -y chromium chromium-driver
RUN mkdir -p plugin_envs && mkdir -p attachments && mkdir -p state
COPY src/ ./src/
COPY builtins/ ./builtins/
COPY setup.sh ./setup.sh
RUN chmod +x ./setup.sh
ENV PYTHONPATH="/app/src"
CMD ["python", "src/email_pipeline/main.py"]