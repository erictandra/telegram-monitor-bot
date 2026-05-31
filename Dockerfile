# ── Stage: runtime ──────────────────────────────────────────────────────────────
FROM python:3.12-slim

LABEL maintainer="you"
LABEL description="Telegram bot monitor laptop Ubuntu"

RUN apt-get update && apt-get install -y --no-install-recommends \
        lm-sensors \
        acpi \
        curl \
        openssh-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

VOLUME ["/app/data"]

ENV BOT_TOKEN=""
ENV CHAT_ID=""
ENV SSH_KEY_LOCATION=""
ENV SSH_USER_NAME=""

CMD ["python", "-u", "bot.py"]
