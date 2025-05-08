FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    gcc \
    python3-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /codenames
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=codenames.settings

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]