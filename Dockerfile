# ── Stage: runtime ──────────────────────────────────────────────────────────────
FROM python:3.12-slim

LABEL maintainer="you"
LABEL description="Telegram bot monitor laptop Ubuntu"

# Install system tools needed to read sensors & run shutdown
# lm-sensors  → suhu CPU
# acpi        → info baterai (fallback)
RUN apt-get update && apt-get install -y --no-install-recommends \
        lm-sensors \
        acpi \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

# Volume untuk menyimpan config.json (max suhu persisten)
VOLUME ["/app/data"]

# Env variable wajib diisi saat run/deploy
ENV BOT_TOKEN=""
ENV CHAT_ID=""

CMD ["python", "-u", "bot.py"]
