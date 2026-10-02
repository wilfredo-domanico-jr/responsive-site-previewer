# Matches the pinned playwright==1.63.0 in requirements.txt; the image ships Chromium
# and every OS library it needs, so no `playwright install` step is required.
FROM mcr.microsoft.com/playwright/python:v1.63.0-noble

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SCREENSHOT_DIR=/app/screenshots

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
RUN mkdir -p /app/screenshots

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
