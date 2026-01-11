FROM python:3.13-slim
WORKDIR /app
RUN mkdir -p plugin_envs && mkdir -p attachments && mkdir -p state
COPY src/ ./src/
COPY plugins/ ./plugins/
COPY .env .env
ENV PYTHONPATH="/app/src"
CMD ["python", "src/mail_pipeline/main.py"]